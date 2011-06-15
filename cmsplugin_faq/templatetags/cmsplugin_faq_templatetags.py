from django import template
from cmsplugin_faq.models import FaqEntry
from django.core.cache import cache
register = template.Library()



class LatestFAQsNode(template.Node):
    """
    parses & checks arguments passed to ``get_latest_faqs``; returns applicable Queryset of recently added CMSFaqPlugin models descendant from and including the current page
    """

    def __init__(self, num, varname):
        num, varname

        #'All' means slicing with [:None] , which returns everything
        if num == 'All' or num == 'all':
            num = None
        else:
            num = abs(int(num))
        self.num = num

        self.varname = varname

    def render(self, context):

        #shortcircuit for django admin
        if context.has_key('current_page'):
            page = context['current_page']

            if page is 'dummy':
                return ''

            #check cache first
            if cache.get('cmsplugin_faq_templatetags_get_latest_faqs'):                                     #if latest_pages exists in cache, return it immediately
                 context[self.varname] = cache.get('cmsplugin_faq_templatetags_get_latest_faqs')
            else:
                #apparently publisher_is_draft has different meanings depending on the status of CMS_MODERATOR?
                from django.conf import settings
                if settings.CMS_MODERATOR:
                    #this seems logical
                    PUBLISHER_STATE = False
                else:
                    #this does not seem logical
                    PUBLISHER_STATE = True

                #get published descendant Pages of the current Page
                subpages = page.get_descendants().filter(publisher_is_draft=PUBLISHER_STATE)

                #list of all published faq plugins for descendant and current page
                allfaqs= []

                #get published plugins for this page
                for faq in page.cmsplugin_set.filter(plugin_type='CMSFaqEntryPlugin', publisher_is_draft=PUBLISHER_STATE):
                    allfaqs.append(faq)

                #get published plugins for each subpage
                for subpage in subpages:
                    for subpagefaq in subpage.cmsplugin_set.filter(plugin_type='CMSFaqEntryPlugin', publisher_is_draft=PUBLISHER_STATE):
                        allfaqs.append(subpagefaq)

                #shortened list according to given argument
                #putting this here for performance reasons?
                context[self.varname] = allfaqs[:self.num]

                cache.set('cmsplugin_faq_templatetags_get_latest_faqs', context[self.varname])               #add latest_pages to the django cache

        return ''

@register.tag('get_latest_faqs')
def get_latest_faqs(parser, token):
    """
    A django-cms templatetag for returning recently added CMSFaqPlugin models.
    Note that the tag only returns Faq plugins descendant from the current page.

    Some common case examples::

        {% get_latest_faqs All as latest_faqs %}
        {% for latest in latest_faqs %}
            ...
        {% endfor %}

        {% get_latest_faqs 3 as latest_faqs %}
        {% for latest in latest_faqs %}
            ...
        {% endfor %}

    Supported arguments are: ``All``, ``all``, positive integers, and zero
    """

    #split up arguments
    bits = token.split_contents()

    #knock off the first argument
    bits.pop(0)
    num = bits[0]
    varname = bits[2]

    if len(bits) != 3:
        raise template.TemplateSyntaxError, "get_latest tag takes exactly three arguments"
    if bits[1] != 'as':
        raise template.TemplateSyntaxError, "second argument to get_latest tag must be 'as'"
    return LatestFAQsNode(num, varname)