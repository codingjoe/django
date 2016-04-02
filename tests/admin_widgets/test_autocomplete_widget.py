from django import forms
from django.contrib.admin.widgets import AutocompleteSelect
from django.forms import ModelChoiceField
from django.test import TestCase, override_settings

from .models import Album, Band
from .widgetadmin import site

model_admin = site._registry[Album]


class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['band']
        widgets = {'band': AutocompleteSelect(model_admin)}


class NotRequiredBandForm(forms.Form):
    band = ModelChoiceField(
        queryset=Album.objects.all(),
        widget=AutocompleteSelect(model_admin),
        required=False,
    )


class RequiredBandForm(forms.Form):
    band = ModelChoiceField(
        queryset=Album.objects.all(),
        widget=AutocompleteSelect(model_admin),
        required=True,
    )


@override_settings(ROOT_URLCONF='admin_widgets.urls')
class AutocompleteMixinTest(TestCase):
    def test_build_attrs(self):
        w = AutocompleteSelect(model_admin, attrs={'class': 'my-class'})
        attrs = w.build_attrs(name='my_field')
        self.assertIn('class', attrs)
        self.assertIn('my-class', attrs['class'])
        self.assertIn('admin-autocomplete', attrs['class'])

        self.assertIn('data-field_identifier', attrs)
        self.assertEqual('admin_widgets.Album.my_field', attrs['data-field_identifier'])

        form = NotRequiredBandForm()
        attrs = form['band'].field.widget.build_attrs(name=form['band'].html_name)
        self.assertJSONEqual(attrs['data-allow-clear'], True)

        form = RequiredBandForm()
        attrs = form['band'].field.widget.build_attrs(name=form['band'].html_name)
        self.assertJSONEqual(attrs['data-allow-clear'], False)

    def test_get_field_identifier(self):
        w = AutocompleteSelect(model_admin)
        form_prefix = 'my-long_form-prefix'

        form = AlbumForm(prefix=form_prefix)
        field_identifier = w.get_field_identifier(name=form['band'].html_name)
        self.assertEqual('admin_widgets.Album.band', field_identifier)

        w = AutocompleteSelect(model_admin)
        form = AlbumForm(prefix='')
        field_identifier = w.get_field_identifier(name=form['band'].html_name)
        self.assertEqual('admin_widgets.Album.band', field_identifier)

    def test_get_url(self):
        w = AutocompleteSelect(model_admin)
        url = w.get_url()
        self.assertEqual(url, '/autocomplete/')

    def test_render_options(self):
        beatles = Band.objects.create(name='The Beatles', style='rock')
        who = Band.objects.create(name='The Who', style='rock')
        form = AlbumForm(initial={'band': beatles.pk})
        output = form.as_table()
        selected_option = '<option value="%s" selected="selected">The Beatles</option>'
        selected_option %= beatles.pk
        option = '<option value="%s">The Who</option>'
        option %= who.pk
        self.assertIn(selected_option, output)
        self.assertNotIn(option, output)

        form = NotRequiredBandForm()
        output = form.as_table()
        self.assertIn('<option></option>', output)

        form = RequiredBandForm()
        output = form.as_table()
        self.assertNotIn('<option></option>', output)
