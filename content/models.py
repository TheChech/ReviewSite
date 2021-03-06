from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.template import Context, Template
import copy

class Content(models.Model):
    """Basic page data which can be used by other modules"""
    renderable_attrs = (
        'title', 'html_title', 'meta_desc', 'keywords', 'content'
    )

    title = models.CharField(max_length=200)
    html_title = models.CharField(max_length=200)
    meta_desc = models.CharField(max_length=200)
    keywords = models.CharField(max_length=200)
    content = models.TextField()

    def render(self, values):
        """Replace the placeholder names with the values and return
        a cloned instance containing the rendered values"""
        cloned = copy.copy(self)
        context = Context(values)

        for attr in self.renderable_attrs:
            string = getattr(self, attr)
            string = self.render_string(string, context)
            setattr(cloned, attr, string)

        return cloned

    def render_string(self, string, context):
        """Render a single value in a string"""
        t = Template(string)
        return t.render(context)

    class Meta:
        abstract = True


class Page(Content):
    """Concrete implementation of a basic page managed by the admin"""
    slug = models.SlugField()

    @property
    def url(self):
        """Get the url for the page based on urls.py"""
        return reverse('page', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title
    

class SystemPage(Content):
    """A page which is required by the site to function,
    such as the home page or 404"""
    name = models.CharField(max_length=200)

    @property
    def url(self):
        """System pages don't really have a url,
        apart from the home page, so just link to that"""
        return reverse('index')

    def __str__(self):
        return self.name


class Menu(models.Model):
    """A group of navigation links"""
    name = models.CharField(max_length=200, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')

    def __str__(self):
        return self.name


class MenuLink(models.Model):
    """A single navigation item"""
    menu = models.ForeignKey(Menu, related_name='links')

    # slightly hacky way of linking a menu to any model
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey()

    text = models.CharField(max_length=200)
    static_url = models.CharField(max_length=200, blank=True)
    order = models.IntegerField()

    @property
    def url(self):
        """Get the url either from the associated object or the hardcoded url, which takes precedence"""
        if(static_url):
            return static_url
        elif(self.content_object):
            return self.content_object.url

    class Meta:
        ordering = ['order']