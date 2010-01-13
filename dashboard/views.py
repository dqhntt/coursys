#from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from coredata.models import Member
from courselib.auth import requires_course_by_slug

@login_required
def index(request):
    # TODO: should distinguish student/TA/instructor roles in template
    userid = request.user.username
    memberships = Member.objects.exclude(role="DROP").filter(offering__graded=True).filter(person__userid=userid) \
            .select_related('offering','person','offering__semester')
    return render_to_response("dashboard/index.html", {'memberships': memberships}, context_instance=RequestContext(request))

@requires_course_by_slug()
def course(request, course_slug):
    """
    Course front page
    """
    return render_to_response("dashboard/course.html", {}, context_instance=RequestContext(request))

