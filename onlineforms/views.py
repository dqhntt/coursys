from datetime import datetime
from django.contrib import messages
from django import forms
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from courselib.auth import NotFoundResponse, ForbiddenResponse, requires_role

# FormGroup management views
from onlineforms.forms import FieldForm
from onlineforms.fieldtypes import *
from onlineforms.forms import FieldForm, DynamicForm
from onlineforms.models import Form, Sheet, Field, FIELD_TYPE_MODELS

from log.models import LogEntry

def manage_groups(request):
    pass


def new_group(request):
    pass


def manage_group(request, formgroup_slug):
    pass


def add_group_member(request, formgroup_slug):
    pass


def remove_group_member(request, formgroup_slug, userid):
    pass

# Form admin views

def list_all(request):
    pass


def new_form(request):
    pass


def view_form(request, form_slug):
    form = get_object_or_404(Form, slug=form_slug)
    form_sheets = Sheet.objects.filter(form=form)

    # need to divide up fields based on sheets (DIVI)
    forms = []
    for sheet in form_sheets:
        form = DynamicForm(sheet.title)
        fieldargs = {}
        fields = Field.objects.filter(sheet=sheet)
        for field in fields:
            field.config['required'] = field.required
            display_field = FIELD_TYPE_MODELS[field.fieldtype](field.config)
            fieldargs[field.id] = display_field.make_entry_field()
        form.setFields(fieldargs)
        forms.append(form)

    context = {'forms': forms}
    return render(request, "onlineforms/view_form.html", context)


def edit_form(request, form_slug):
    pass


def new_sheet(request, form_slug):
    pass


def edit_sheet(request, form_slug, sheet_slug):
    # http://127.0.0.1:8000/forms/comp-test-form-2/edit/initial-sheet/
    owner_form = get_object_or_404(Form, slug=form_slug)
    owner_sheet = get_object_or_404(Sheet, form=owner_form, slug=sheet_slug)
    fields = Field.objects.filter(sheet=owner_sheet, active=True).order_by('order')

    # check if they are deleting a field from the sheet
    if request.method == 'POST' and 'action' in request.POST and request.POST['action']=='del':
        field_id = request.POST['field_id']
        fields = Field.objects.filter(id=field_id, sheet=owner_sheet)
        # TODO handle the condition where we cant find the field
        if fields:
            field = fields[0]
            field.active = False
            field.save()
            messages.success(request, 'Removed the field %s.' % (field.label))
        return HttpResponseRedirect(reverse(edit_sheet, kwargs={'form_slug': owner_form.slug, 'sheet_slug': owner_sheet.slug}))

    # construct a form from this sheets fields
    form = DynamicForm(owner_sheet.title)
    fieldargs = {}
    for field in fields:
        field.config['required'] = field.required
        display_field = FIELD_TYPE_MODELS[field.fieldtype](field.config)
        fieldargs[field.id] = display_field.make_entry_field()
    form.setFields(fieldargs)

    context = {'owner_form': owner_form, 'owner_sheet': owner_sheet, 'form': form, 'fields': fields}
    return render(request, "onlineforms/edit_sheet.html", context)


def new_field(request, form_slug, sheet_slug):
    #Test url: http://localhost:8000/forms/comp-test-form-1/edit/initial-sheet/new
    #TODO: Add proper security checks.

    owner_sheet = get_object_or_404(Sheet, slug=sheet_slug)
    section = 'select'
    type = None

    if request.method == 'POST':
        if 'next_section' in request.POST:
            section = request.POST['next_section']
        if section == 'config':
            custom_config = {}
            if 'type' in request.POST:
                type = request.POST['type']
                type_model = FIELD_TYPE_MODELS[type]
                field = type_model()

            else:
                type = request.POST['type_name']
                type_model = FIELD_TYPE_MODELS[type]
                custom_config = _clean_config(request.POST)
                field = type_model(config=custom_config)

            form = field.make_config_form()
            if form.is_valid():
                Field.objects.create(label=form.cleaned_data['label'],
                    sheet=owner_sheet,
                    required=form.cleaned_data['required'],
                    fieldtype=type,
                    config=custom_config,
                    active=True,
                    original=None,
                    created_date=datetime.now(),
                    last_modified=datetime.now())
                messages.success(request, 'Successfully created the new field \'%s\'' % form.cleaned_data['label'])
                section = 'select'

        if section == 'select':
            form = FieldForm()
            section = 'config'
    else:
        form = FieldForm()
        section = 'config'

    context = {'form': form, 'slug_form': form_slug, 'slug_sheet': sheet_slug, 'section': section, 'type_name': type}
    return render(request, 'onlineforms/new_field.html', context)


def _clean_config(config):
    irrelevant_fields = ['csrfmiddlewaretoken', 'next_section', 'type_name']
    clean_config = {key: value for (key, value) in config.iteritems() if key not in irrelevant_fields}
    if 'required' not in clean_config:
        clean_config['required'] = False

    return clean_config


def edit_field(request, form_slug, sheet_slug, field_slug):
    #Test url: http://localhost:8000/forms/comp-test-form-1/edit/initial-sheet/*label of a field*

    owner_sheet = get_object_or_404(Sheet, slug=sheet_slug)
    field = get_object_or_404(Field, slug=field_slug)

    if request.POST:
        clean_config = _clean_config(request.POST)
        form = FIELD_TYPE_MODELS[field.fieldtype](config=clean_config).make_config_form()

        if form.is_valid():
            field.active = False

            new_field = Field.objects.create(label=form.cleaned_data['label'],
                sheet=owner_sheet,
                required=form.cleaned_data['required'],
                fieldtype=field.fieldtype,
                config=clean_config,
                active=True,
                original=field,
                created_date=field.created_date,
                last_modified=datetime.now())
            messages.success(request, 'Successfully updated the new field \'%s\'' % form.cleaned_data['label'])

            field.save()
            field_slug = new_field.slug


    else:
        form = FIELD_TYPE_MODELS[field.fieldtype](config=field.config).make_config_form()

    context = {'form': form, 'slug_form': form_slug, 'slug_sheet': sheet_slug, 'slug_field': field_slug}
    return render(request, 'onlineforms/edit_field.html', context)

# Form-filling views

def view_submission(request, form_slug, formsubmit_slug):
    pass


def sheet_submission(request, form_slug, sheet_slug):
    pass
