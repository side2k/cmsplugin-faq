from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin, Page
from django.conf import settings
from django.utils.html import strip_tags
from django.utils.text import truncate_words
from cms.plugins.text.utils import plugin_admin_html_to_tags, plugin_tags_to_admin_html
from django.conf import settings


#get custom css from settings or use default
CMSPLUGIN_FAQENTRY_CSS_CHOICES = getattr(settings,"CMSPLUGIN_FAQENTRY_CSS_CHOICES", (('1', 'featured'),) )

class FaqEntry(CMSPlugin):
    """Copy of Text plugin model, plus additional 'topic' Charfield"""
    topic = models.CharField(_("Topic"),max_length=500, help_text=_('FAQ entry topic'))
    css = models.CharField(_('CSS class'), max_length=1, choices=CMSPLUGIN_FAQENTRY_CSS_CHOICES, blank=True, help_text=_('Additional CSS class to apply'))
    body = models.TextField(_("body"))

    def _set_body_admin(self, text):
        self.body = plugin_admin_html_to_tags(text)

    def _get_body_admin(self):
        return plugin_tags_to_admin_html(self.body)

    body_for_admin = property(_get_body_admin, _set_body_admin, None,
                              """
                              body attribute, but with transformations
                              applied to allow editing in the
                              admin. Read/write.
                              """)

    search_fields = ('topic', 'body',)

    def get_absolute_url(self):
        """ returns url pointing to the anchor in the cms Page containing the FaqEntry plugin """

        #use django's slugify for the href anchor (e.g.: remove non-ASCII characters)
        from django.template.defaultfilters import slugify

        #create the FaqEntry's url as a combination of the Page's url + '#' + the slugified anchor
		# modified by atknet.ru 2010-06-28
        #url = "%s#%s" % (self.page.get_absolute_url(language=self.language, fallback=False), slugify(self.topic))
        url = "%s#%s" % (self.page.get_absolute_url(language=self.language, fallback=False), self.id)

#        import ipdb; ipdb.set_trace()

        #supposedly the following is not necessary. but i haven't been able to get it working with multilingual otherwise
        #check if multilingual middleware is installed
        if 'cms.middleware.multilingual.MultilingualURLMiddleware' in settings.MIDDLEWARE_CLASSES:
            #prepend language namespace (better way to do this?)
            url = '/' + self.language + url

        return url

    def __unicode__(self):
        return u"%s" % (truncate_words(self.topic, 5)[:30]+"...")


#get custom css from settings or use default
CMSPLUGIN_FAQLIST_CSS_CHOICES = getattr(settings,"CMSPLUGIN_FAQLIST_CSS_CHOICES", (('1', 'faq-list'),('2', 'faq-list-small'),) )

class FaqList(CMSPlugin):
    """Model to give FaqList plugin various options"""
    truncate_body = models.PositiveSmallIntegerField(_('Truncate words'), default=5, help_text=_('Truncate FAQ Entry body by this many words; zero means Django default'))
    show_body = models.BooleanField(_('Show FAQ Entry body'),default=True)
    css = models.CharField(_('CSS class'), max_length=1, choices=CMSPLUGIN_FAQLIST_CSS_CHOICES, blank=True, help_text=_('Additional CSS class to apply'))

    def __unicode__(self):
        return u"%s" % (self.page.get_page_title())


#get custom css from settings or use default
CMSPLUGIN_FAQENTRYLINK_CSS_CHOICES = getattr(settings,"CMSPLUGIN_FAQENTRYLINK_CSS_CHOICES", (('1', 'faq-entry-link-small'),) )

class FaqEntryLink(CMSPlugin):
    """Model to give FaqEntryLink plugin various options"""
    link = models.ForeignKey(FaqEntry, limit_choices_to={'publisher_is_draft': False}, blank=True, null=True, verbose_name=_('Linked FAQ Entry'), help_text=_('Leave empty for random'))
    truncate_body = models.PositiveSmallIntegerField(_('Truncate words'), default=5, help_text=_('Truncate FAQ Entry body by this many words; zero means Django default'))
    show_body = models.BooleanField(_('Show FAQ Entry body'),default=True)
    css = models.CharField(_('CSS class'), max_length=1, choices=CMSPLUGIN_FAQENTRYLINK_CSS_CHOICES, blank=True, help_text=_('Additional CSS class to apply'))

    def __unicode__(self):
        return u"FAQ Entry %s" % (self.link)