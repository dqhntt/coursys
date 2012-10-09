from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from courselib.auth import NotFoundResponse, ForbiddenResponse, requires_role

# FormGroup management views

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
    pass


def edit_form(request, form_slug):
    pass


def new_sheet(request, form_slug):
    pass


def edit_sheet(request, form_slug, sheet_slug):
    pass


def new_field(request, form_slug, sheet_slug):
    context = {}
    return render(request, 'onlineforms/new_field.html', context)
    pass


def edit_field(request, form_slug, sheet_slug, field_slug):
    context = {}
    return render(request, 'onlineforms/edit_field.html', context)
    pass

# Form-filling views

def view_submission(request, form_slug, formsubmit_slug):
    pass


def sheet_submission(request, form_slug, sheet_slug):
    pass

