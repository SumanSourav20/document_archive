import datetime
from pathlib import Path
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django_softdelete.models import SoftDeleteModel
import base64
if settings.AUDIT_LOG_ENABLED:
    from auditlog.registry import auditlog

User = get_user_model()

class Project(models.Model):
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    ON_HOLD = 'on_hold'
    CANCELLED = 'cancelled'
    UNKNOWN = 'unknown'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
        (ON_HOLD, 'On Hold'),
        (CANCELLED, 'Cancelled'),
        (UNKNOWN, 'Unknown')
    ]

    title = models.CharField(_("title"), max_length=512, db_index=True)

    description = models.CharField(max_length=2048, blank=True, null=True)

    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=UNKNOWN,
    )

    start_date = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = _("project")
        verbose_name_plural = _("projects")


class Correspondent(models.Model):
    name = models.CharField(_("name"), max_length=255, db_index=True)

    class Meta:
        verbose_name = _("correspondent")
        verbose_name_plural = _("correspondents")


class Tag(models.Model):
    name = models.CharField(_("name"), max_length=255, db_index=True)
    
    color = models.CharField(_("color"), max_length=7, default="#a6cee3")

    is_inbox_tag = models.BooleanField(
        _("is inbox tag"),
        default=False,
        help_text=_(
            "Marks this tag as an inbox tag: All newly consumed "
            "documents will be tagged with inbox tags.",
        ),
    )

    class Meta():
        verbose_name = _("tag")
        verbose_name_plural = _("tags")

        
class DocumentType(models.Model):
    name = models.CharField(_("name"), max_length=255)
    
    class Meta:
        verbose_name = _("document type")
        verbose_name_plural = _("document types")


class StoragePath(models.Model):
    path = models.TextField(
        _("path"),
    )

    class Meta:
        verbose_name = _("storage path")
        verbose_name_plural = _("storage paths")


class Document(SoftDeleteModel):
    STORAGE_TYPE_UNENCRYPTED = _("unencrypted")
    STORAGE_TYPE_GPG = _("gpg")
    STORAGE_TYPES = (
        (STORAGE_TYPE_UNENCRYPTED, "Unencrypted"),
        (STORAGE_TYPE_GPG, "Encrypted with GNU Privacy Guard"),
    )

    project = models.ForeignKey(
        Project,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="documents",
        verbose_name=_("projects")
    )

    correspondent = models.ForeignKey(
        Correspondent,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="documents",
        verbose_name=_("correspondent")
    )

    storage_path = models.ForeignKey(
        StoragePath,
        blank=True,
        null=True,
        related_name="documents",
        on_delete=models.SET_NULL,
        verbose_name=_("storage path"),
    )

    title = models.CharField(_("title"), max_length=255, blank=True, db_index=True)

    document_type = models.ForeignKey(
        DocumentType,
        blank=True,
        null=True,
        related_name="documents",
        on_delete=models.SET_NULL,
        verbose_name=_("document type"),
    )

    mime_type = models.CharField(_("mime type"), max_length=256, editable=False)

    tags = models.ManyToManyField(
        Tag,
        related_name="documents",
        blank=True,
        verbose_name=_("tags"),
    )
    
    page_count = models.PositiveIntegerField(
        _("page count"),
        blank=False,
        null=True,
        unique=False,
        db_index=False,
        validators=[MinValueValidator(1)],
        help_text=_(
            "The number of pages of the document.",
        ),
    )

    checksum = models.CharField(
        _("checksum"),
        max_length=32,
        editable=False,
        unique=True,
        help_text=_("The checksum of the original document."),
    )

    archive_checksum = models.CharField(
        _("archive checksum"),
        max_length=32,
        editable=False,
        blank=True,
        null=True,
        help_text=_("The checksum of the archived document."),
    )

    created = models.DateTimeField(
        _("created"), 
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Document Creation or Generation Date")
    )

    modified = models.DateTimeField(
        _("modified"),
        auto_now=True,
        editable=False,
        db_index=True,
    )

    storage_type = models.CharField(
        _("storage type"),
        max_length=11,
        choices=STORAGE_TYPES,
        default=STORAGE_TYPE_UNENCRYPTED,
        editable=False,
    )

    added = models.DateTimeField(
        _("added"),
        default=timezone.now,
        editable=False,
        db_index=True,
    )

    filename = models.FilePathField(
        _("filename"),
        max_length=1024,
        editable=False,
        default=None,
        unique=True,
        null=True,
        help_text=_("Current filename in storage"),
    )

    archive_filename = models.FilePathField(
        _("archive filename"),
        max_length=1024,
        editable=False,
        default=None,
        unique=True,
        null=True,
        help_text=_("Current archive filename in storage"),
    )

    original_filename = models.CharField(
        _("original filename"),
        max_length=1024,
        editable=False,
        default=None,
        unique=False,
        null=True,
        help_text=_("The original name of the file when it was uploaded"),
    )

    class Meta:
        ordering = ("-created",)
        verbose_name = _("document")
        verbose_name_plural = _("documents")

    def __str__(self) -> str:

        created = datetime.date.isoformat(timezone.localdate(self.created))

        res = f"{created}"

        if self.correspondent:
            res += f" {self.correspondent}"
        if self.title:
            res += f" {self.title}"
        return res
    
    @property
    def has_archive_version(self) -> bool:
        return self.archive_filename is not None 
    
    @property
    def archive_path(self) -> Path | None:
        if self.has_archive_version:
            return  (settings.ARCHIVE_DIR/ Path(str(self.archive_filename))).resolve()
        else:
            return None
       
    @property
    def archive_file(self):
        if self.archive_path:
            return Path(self.archive_path).open("rb")
        else:
            return None

    @property
    def source_path(self) -> Path:
        fname = str(self.filename)
        if self.storage_type == self.STORAGE_TYPE_GPG:
            fname += ".gpg"
        
        return (settings.ORIGINAL_DIR / Path(fname)).resolve()
    
    @property
    def source_file(self): 
        return Path(self.source_path).open("rb")
    
    @property
    def thumbnail_path(self) -> Path:
        webp_file_name = f"{self.pk:07}.webp"
        if self.storage_type == self.STORAGE_TYPE_GPG:
            webp_file_name += ".gpg"

        webp_file_path = settings.THUMBNAIL_DIR / Path(webp_file_name)

        return webp_file_path.resolve()
    
    @property
    def thumbnail_str(self):
        file_path = Path(self.thumbnail_path)
        if file_path.exists():
            return base64.b64encode(file_path.open("rb").read()).decode('utf-8')
        else:
            return None
    
    @property
    def created_date(self):
        return self.created
    

class Note(SoftDeleteModel):
    note = models.TextField(
        _("content"),
        blank=True,
        help_text=_("Note for the document"),
    )

    created = models.DateTimeField(
        _("created"),
        default=timezone.now,
        db_index=True,
    )

    document = models.ForeignKey(
        Document,
        related_name="notes",
        on_delete=models.CASCADE,
        verbose_name=_("document"),
    )

    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name="notes",
        on_delete=models.SET_NULL,
        verbose_name=_("user"),
    )

    class Meta:
        ordering = ("created",)
        verbose_name = _("note")
        verbose_name_plural = _("notes")

    def __str__(self):
        return self.note
    

if settings.AUDIT_LOG_ENABLED:
    auditlog.register(
        Document,
        m2m_fields={"tags"},
        exclude_fields=["modified"],
    )
    auditlog.register(Correspondent)
    auditlog.register(Tag)
    auditlog.register(DocumentType)
    auditlog.register(Note)
    
