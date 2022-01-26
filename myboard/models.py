from django.db import models
from django.contrib.auth.models import BaseUserManager
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.validators import UnicodeUsernameValidator

from django.apps import apps
from django.contrib.auth.hashers import make_password

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

class MyUserManager(BaseUserManager):

    def _create_user(self, username, email, password,**extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        GlobalUserModel = apps.get_model(self.model._meta.app_label, self.model._meta.object_name)
        username = GlobalUserModel.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None,**extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_labpc', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_labpc', False)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(username, email, password, **extra_fields)
        

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Username and password are required. Other fields are optional.
    """
    class Meta:
        verbose_name_plural = "Accounts"
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    is_labpc = models.BooleanField(
        default=False,
        help_text=_(
            'User for LabPC'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = MyUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

class LABPC(models.Model):
    """lab PC.

    Attributes:
        user: username.

    """

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True)
    username = models.CharField(max_length=255, null=True,default= None,blank=True,editable = False,unique=True)
    ipaddr = models.CharField(max_length=255, null=True, blank=True)
    port = models.IntegerField(default=0, blank=True)
    def __str__(self):
        return "(%s) labpc_%s" % (str(self.id), self.username)

@receiver(post_save, sender=LABPC)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        instance.username = instance.user.username
        instance.save()



class PCD(models.Model):
    """Power control device.

    Attributes:
        type: type of device.
        ipaddr: IP of device.
        gateway: gateway.
        netmark: netmark.
        port: port number.
        LABPCOwner: owner of Lab PC.

    """

    name = models.CharField(max_length=255)

    class Type(models.IntegerChoices):
        """type of power control device."""
        TYPE1 = 1
        TYPE2 = 2

    type = models.IntegerField(default=Type.TYPE1, choices=Type.choices)
    ipaddr = models.CharField(max_length=255, null=True, blank=True)
    gateway = models.CharField(max_length=255, null=True, blank=True)
    netmark = models.CharField(max_length=255, null=True, blank=True)
    port = models.IntegerField(default=0, blank=True)
    LABPCOwner = models.ForeignKey(LABPC, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return "(%s) pcd_%s" % (str(self.id), self.LABPCOwner.user.username)


class Board(models.Model):
    """Board properties.

    Attributes:
        displayName: board name.
        boardType: Type of board
        holder: board keeper.
        PCDOwner: owner of power control device.
        LABPCOwner: owner of lab PC.
        powerSwitchRelayNumber: power status.
        accSwitchRelayNumber: boot status.
        isActivate: is board on the lab PC?
        isUsing: is board ready to use?
        isShareControl: share status.

    """

    UNK = 'UNK'
    S4 = 'S4'
    V3H1 = 'V3H1'
    V3H2 = 'V3H2'
    V3U = 'V3U'
    BOARD_TYPE_CHOICES = [
        (UNK,'Unknown'),
        (S4, 'Spider'),
        (V3H1, 'Condor'),
        (V3H2, 'Condor-I'),
        (V3U, 'Falcon')
    ]
    
    def __str__(self):
        return "(%s) %s" % (str(self.id), self.displayName)

    class StatusPower(models.IntegerChoices):
        """type of power status."""

        POWER_OFF = 0
        POWER_ON = 1
    class StatusBoot(models.IntegerChoices):
        """type of power status."""

        BOOT = 0
        UNBOOT = 1
    displayName = models.CharField(max_length=255)
    boardLabID =  models.IntegerField(default = -1)
    boardType = models.CharField(max_length=255,choices=BOARD_TYPE_CHOICES,default=UNK)
    usbSerialNumber = models.CharField(max_length=255,default = None,null=True,blank = True)
    boardUniqueSerialNumber = models.CharField(max_length=255,default = None,unique=True,null=True,blank = True)
    holder = models.ForeignKey(CustomUser, on_delete=models.CASCADE,blank = True,null=True)
    PCDOwner = models.ForeignKey(PCD, on_delete=models.CASCADE) 
    LABPCOwner = models.ForeignKey(LABPC, on_delete=models.CASCADE,editable=False) 
    powerSwitchRelayNumber = models.IntegerField(default=-1)
    accSwitchRelayNumber = models.IntegerField(default=-1)
    isActivate = models.BooleanField(default=False)
    isUsing = models.BooleanField(default=False)
    isShareControl = models.BooleanField(default=True)
    usingBy = models.CharField(default = None ,max_length=255,editable=False,null=True,blank = True)
    statusPower = models.IntegerField(default=StatusPower.POWER_OFF,choices=StatusPower.choices)
    statusBoot = models.IntegerField(default=StatusBoot.BOOT,choices=StatusBoot.choices)
    anonymousToken = models.CharField(default = None ,max_length=255,editable=False,null=True,blank = True)

    def save(self, *args, **kwargs):
        self.LABPCOwner = self.PCDOwner.LABPCOwner
        self.LABPCOwner.save()
        super().save(*args, **kwargs)
