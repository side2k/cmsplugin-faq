from cms.plugin_pool import plugin_pool
from cms.plugin_base import CMSPluginBase
from cms.models import CMSPlugin
from django.utils.translation import ugettext_lazy as _
from models import FaqEntry, FaqList, FaqEntryLink
from forms import FaqEntryForm
from cms.plugins.text.widgets.wymeditor_widget import WYMEditor
from cms.plugins.text.utils import plugin_tags_to_user_html
from cms.plugins.text.utils import plugin_admin_html_to_tags, plugin_tags_to_admin_html
from django.utils.text import truncate_words
from django.forms.fields import CharField, BooleanField
from django.forms import TextInput
from cms.plugins.text.settings import USE_TINYMCE
from django.conf import settings


class CMSFaqEntryPlugin(CMSPluginBase):
    """Copy of Text plugin, includes 'topic' Charfield"""

    model = FaqEntry
    name = _("FAQ Entry")
    form = FaqEntryForm
    render_template = "plugins/cmsplugin_faq/faq_entry.html"
    change_form_template = "cms/plugins/text_plugin_change_form.html"

    def get_editor_widget(self, request, plugins):
        """
        Returns the Django form Widget to be used for
        the text area
        """
        if USE_TINYMCE and "tinymce" in settings.INSTALLED_APPS:
            from cms.plugins.text.widgets.tinymce_widget import TinyMCEEditor
            return TinyMCEEditor(installed_plugins=plugins)
        else:
            return WYMEditor(installed_plugins=plugins)

    def get_form_class(self, request, plugins):
        """
        Returns a subclass of Form to be used by this plugin
        """
        # We avoid mutating the Form declared above by subclassing
        class FaqEntryPluginForm(self.form):
            pass

        widget = self.get_editor_widget(request, plugins)
        FaqEntryPluginForm.declared_fields["body"] = CharField(widget=widget, required=False)
        return FaqEntryPluginForm

    def get_form(self, request, obj=None, **kwargs):
        page = None
        if obj:
            page = obj.page
        plugins = plugin_pool.get_text_enabled_plugins(self.placeholder)
        form = self.get_form_class(request, plugins)
        kwargs['form'] = form # override standard form
        return super(CMSFaqEntryPlugin, self).get_form(request, obj, **kwargs)

    def render(self, context, instance, placeholder):
        from django.template.defaultfilters import slugify
        context.update({
            'body': plugin_tags_to_user_html(instance.body, context, placeholder),
            'topic': instance.topic,
            'name': slugify(instance.topic),
            'css': instance.get_css_display(),
            'placeholder': placeholder,
            'object': instance,
        })
        return context

plugin_pool.register_plugin(CMSFaqEntryPlugin)


class CMSFaqListPlugin(CMSPluginBase):
    """Lists all FaqEntry plugins on the same page as this plugin"""

    model = FaqList
    name = _("FAQ List")
    render_template = "plugins/cmsplugin_faq/faq_list.html"

    def render(self, context, instance, placeholder):

        #get all FaqEntryPlugin on this page and this language
        language = context.get('lang', settings.LANGUAGE_CODE)
        plugins = instance.page.cmsplugin_set.filter(plugin_type='CMSFaqEntryPlugin', language=language)

        faqentry_plugins = []

        #make a list of the faqentry plugin objects
        for plugin in plugins:
            #truncate the entry's body
            if instance.truncate_body:
                plugin.faqentry.body = truncate_words(plugin.faqentry.body, instance.truncate_body)
            #show the entry's body or not
            if not instance.show_body:
                plugin.faqentry.body = ''
            faqentry_plugins.append(plugin.faqentry)

        context.update({
            'faq_list': faqentry_plugins,
            'css': instance.get_css_display(),
            'placeholder': placeholder,
        })

        return context

plugin_pool.register_plugin(CMSFaqListPlugin)


#DOESN'T WORK WITH 2.0.2 & CMS_MODERATOR: published plugin `link` field is blank, so returned link plugin is random
class CMSFaqEntryLinkPlugin(CMSPluginBase):
    """Links to a single FaqEntry plugin"""

    model = FaqEntryLink
    name = _("FAQ Entry Link")
    text_enabled = True
    render_template = "plugins/cmsplugin_faq/faq_entry_link.html"

    def render(self, context, instance, placeholder):

#        import ipdb; ipdb.set_trace()

        #if a faqentry is not specified, choose one at random
        if not instance.link:
            faqentry_plugins = []
            #get all FaqEntryPlugins
            plugins = CMSPlugin.objects.filter(plugin_type='CMSFaqEntryPlugin')
            #make a list of the faqentry plugin objects
            for plugin in plugins:
                faqentry_plugins.append(plugin.faqentry)
            try:
                #choose a random one
                import random
                instance.link = random.sample(faqentry_plugins, 1)[0]
                #set the page id of the linked faqentry
                page_id = instance.link.page_id
            except (ValueError, AttributeError):                    #since this didn't work, we assume no plugin exists
                raise ValueError("No FaqEntryPlugin was returned. Make sure one exists and is published.")

        #truncate the entry's body
        if instance.truncate_body and instance.link.body:
            instance.link.body = truncate_words(instance.link.body, instance.truncate_body)

        #show the entry's body or not
        if not instance.show_body:
            instance.link.body = ''

        context.update({
            'body':plugin_tags_to_user_html(instance.link.body, context, placeholder),
            'topic':instance.link.topic,
            'url': instance.link.get_absolute_url(),
            'placeholder':placeholder,
            'object':instance,
            'css' : instance.get_css_display(),
        })
        return context

plugin_pool.register_plugin(CMSFaqEntryLinkPlugin)
