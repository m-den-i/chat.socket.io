from __future__ import unicode_literals

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.core import validators
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class ConfirmAccountManagerMixin(object):
    def create_superuser(self, email, password, **extra_fields):
        username = email
        return super(ConfirmAccountManagerMixin, self).create_superuser(username, email, password, **extra_fields)


class MemberManager(ConfirmAccountManagerMixin, UserManager):
    pass


class Member(PermissionsMixin, ConfirmAccountManagerMixin, AbstractBaseUser):
    username = models.CharField(
        _('username'),
        max_length=30,
        unique=True,
        help_text=_('Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[
            validators.RegexValidator(
                r'^[\w.@+-]+$',
                _('Enter a valid username. This value may contain only '
                  'letters, numbers ' 'and @/./+/-/_ characters.')
            ),
        ],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), unique=True)
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
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = MemberManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def save(self, *args, **kwargs):
        self.username = self.email
        super(Member, self).save(*args, **kwargs)


class Message(models.Model):
    text = models.TextField(blank=True)
    sent = models.DateTimeField(auto_now_add=True)
    conversation = models.ForeignKey('Conversation', null=True, blank=True, related_name='messages')
    owner = models.ForeignKey('Member', related_name='messages', null=True, blank=True)

    def __unicode__(self):
        return u'' + self.text[:30]


class Conversation(models.Model):
    name = models.CharField(max_length=256)
    members = models.ManyToManyField(Member)

    def __unicode__(self):
        return u'' + self.name