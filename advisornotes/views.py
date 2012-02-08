from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import render_to_response, get_object_or_404, render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from advisornotes.models import AdvisorNote
from coredata.models import Member, Person, Role, Unit
from django.template import RequestContext
from courselib.auth import *
from advisornotes.forms import AdvisorNoteForm, StudentSelect, StudentField, StudentSearchForm
from django.contrib import messages
from courselib.search import get_query
import json

@requires_advisor
def advising(request, student_id=None):
    if student_id:
        student = get_object_or_404(Person, id=student_id)
    else:
        student = None
        
    if request.method == 'POST':
        # find the student if we can and redirect to info page
        form = StudentSearchForm(request.POST)
        if not form.is_valid():
            messages.add_message(request, messages.ERROR, 'Invalid search')
            context = {'form': form}
            return render_to_response('advisornotes/student_search.html', context, context_instance=RequestContext(request))
        search = form.cleaned_data['search']
        return HttpResponseRedirect(reverse('advisornotes.views.student_notes', kwargs={'userid': search.userid}))        
    if student_id:
        form = StudentSearchForm(instance=student, initial={'student': student.userid})
    else:
        form = StudentSearchForm()
    context = {'form': form}
    return render_to_response('advisornotes/student_search.html', context, context_instance=RequestContext(request))

@requires_advisor
def new_note(request,userid):
    student = Person.objects.get(userid = userid)
    depts = Role.objects.filter(person__userid=request.user.username, role='ADVS').values('unit_id')
    unit_choices = Unit.objects.filter(id__in=depts).values_list('id','name')

    if request.method == 'POST':
        form = AdvisorNoteForm(request.POST, request.FILES)
        form.fields['unit'].choices = unit_choices
        if form.is_valid():
            note = form.save(False)
            note.student_id= student.id
            note.advisor_id = Person.objects.get(userid = request.user.username).id

            if 'file_attachment' in request.FILES:
                upfile = request.FILES['file_attachment']
                note.file_mediatype= upfile.content_type
                messages.add_message(request, messages.SUCCESS, 'Created file attachment "%s".' % (upfile.name))
                
            note.save()
            """
            #LOG EVENT#
            l = LogEntry(userid=request.user.username,
                  description=("new note: for %s") % (form.instance.student),
                  related_object=form.instance)
            l.save()
            """
            messages.add_message(request, messages.SUCCESS, 'Note created successfully.' )
            notes = AdvisorNote.objects.filter(student__userid=userid)
            return redirect('..', {'notes': notes, 'student' : student})
            # FIX: the '..' doesn't seem optimal, but I can't find a better way
    else:
        form = AdvisorNoteForm(initial={'student': student })
        form.fields['unit'].choices = unit_choices
    return render(request, 'advisornotes/new_note.html', {'form': form, 'student':student} )
 
@requires_advisor
def view_note(request, userid, note_id):
    note = get_object_or_404(AdvisorNote, pk=note_id)
    student = Person.objects.get(userid=userid)
    return render(request, 'advisornotes/view_note.html', {'note': note, 'student':student}, context_instance=RequestContext(request))

@requires_advisor
def student_notes(request,userid):
    if request.POST:
        if request.is_ajax():
            note = get_object_or_404(AdvisorNote, pk=request.POST['note_id'])
            if request.POST['hide']=="yes":
                note.hidden=True
            else:
                note.hidden=False
            note.save()
            
    depts = Role.objects.filter(person__userid=request.user.username, role='ADVS').values('unit_id')
    notes = AdvisorNote.objects.filter(student__userid=userid, unit__id__in=depts).order_by("-created_at")
    student = Person.objects.get(userid=userid)
    return render(request, 'advisornotes/student_notes.html', {'notes': notes, 'student' : student}, context_instance=RequestContext(request))
    
@requires_advisor
def download_file(request, userid, note_id):
    note = AdvisorNote.objects.get(id = note_id)
    note.file_attachment.open()
    resp = HttpResponse(note.file_attachment, mimetype=note.file_mediatype)
    resp['Content-Disposition'] = 'inline; filename=' + note.attachment_filename()
    return resp

    
