# Python
import datetime
import decimal
# Django
from django.db import models
from django.db.models.query import QuerySet
# Third Party
from model_utils.managers import PassThroughManager
from autoslug import AutoSlugField
# Local
from coredata.models import Unit, Person, CourseOffering, Semester
from courselib.slugs import make_slug
from courselib.json_fields import JSONField
from grad.models import GradStudent
from ra.models import Account


CONTRACT_STATUS_CHOICES = (
        ("NEW","Draft"),
        ("SGN","Signed"),
        ("CAN","Cancelled"),
)


class ContractFrozen(Exception):
    """
    Once a SGNed contract exists within a Category, that Category
        can never be changed again, except to hide it. 
    Once a contract is in the SGN or CAN state, it can't be edited.
        (Except for the state, which can be moved from SGN to CAN).
    To edit a contract that is SGN, that contract must be CANcelled, 
        then copied, then SiGNed again. 
    Movement between the status options is one-way - 
        a NEW contract can become a SGN contract,
        and a SGN contract can become a CAN contract, 
        but a SGN contract can't be changed to a NEW,
        nor can a CAN contract be changed to NEW or SGN.
    """
    pass


class NoPreviousSemesterException(Exception):
    """
    This is thrown when you try to copy the TACategory objects
    from a previous TASemester, but no such TASemester can be 
    found. 
    """
    pass


APPOINTMENT_CHOICES = (
        ("INIT","Initial appointment to this position"),
        ("REAP","Reappointment to same position or revision to appointment"),
)


# These are SIN numbers that we know are probably fake.
DUMMY_SINS = ['999999999', '000000000', '123456789']


class HiringSemesterQuerySet(QuerySet):
    def visible(self, units):
        return self.filter(unit__in=units)
    def semester(self, semester_name, units):
        return self.filter(unit__in=units, 
                           semester=Semester.objects.get(name=semester_name))


class TACategoryQuerySet(QuerySet):
    def visible(self, hiring_semester):
        return self.filter(hiring_semester=hiring_semester, hidden=False)


class TAContractQuerySet(QuerySet):
    def visible(self, hiring_semester):
        return self.filter(category__hiring_semester=hiring_semester)\
                    .select_related('category')\
                    .select_related('email_receipt')\
                    .prefetch_related('course')
    def draft(self, hiring_semester):
        return self.visible(hiring_semester).filter(status='NEW')
    def signed(self, hiring_semester):
        return self.visible(hiring_semester).filter(status='SGN')
    def cancelled(self, hiring_semester):
        return self.visible(hiring_semester).filter(status='CAN')


class HiringSemester(models.Model):
    """
    TA Appointments tend to be a semesterly affair, and each Contract in 
    a Semester is likely to share a single pay_start, pay_end, and set
    of payperiods. 
    This is subject to change on a contract-by-contract basis, 
    so these are only defaults. 
    """
    semester = models.ForeignKey(Semester)
    unit = models.ForeignKey(Unit)
    pay_start = models.DateField()
    pay_end = models.DateField()
    payperiods = models.PositiveIntegerField(
               help_text="During the contract, how many bi-weekly pay periods?")
    config = JSONField(null=False, blank=False, editable=False, default={})
    
    class Meta:
        unique_together = (('semester', 'unit'),)
    
    def __unicode__(self):
        return unicode(self.semester.name)

    def copy_categories_from_previous_semester(self):
        prev_semester = self.semester.previous_semester()
        if prev_semester == None:
            raise NoPreviousSemesterException()
        try:
            hiring_semester = HiringSemester.objects.get(semester=prev_semester)
        except HiringSemester.DoesNotExist:
            raise NoPreviousSemesterException()

        for category in hiring_semester.tacategory_set.objects():
            category.copy_to_new_semester(self)
        
    @property
    def contracts(self):
        return TAContract.objects.visible(self)

    @property
    def number_of_contracts(self):
        return len(self.contracts)

    @property
    def number_of_incomplete_contracts(self):
        incomplete_contracts = [contract for contract in self.contracts 
                                if contract.status == 'NEW']
        return len(incomplete_contracts)

    @property
    def total_bu(self):
        return sum([contract.total_bu for contract in self.contracts])
    
    objects = PassThroughManager.for_queryset_class(HiringSemesterQuerySet)()
    
    def next_export_seq(self):
        """
        For the CSV, 
        we keep track of which batch of exports we're currently on.
        """
        if 'export_seq' in self.config:
            current = self.config['export_seq']
        else:
            current = 0
        
        self.config['export_seq'] = current + 1
        self.save()
        return self.config['export_seq']


class TACategory(models.Model):
    """
    A TACategory details a pay category.
    It's only valid for a single semester, but we offer the ability 
    to copy all of the TACategories from the last semester to the next semester.
    """
    account = models.ForeignKey(Account)
    # the account already FKs to a Unit, so we don't need one. 
    hiring_semester = models.ForeignKey(HiringSemester, editable=False)
    code = models.CharField(max_length=5, 
                        help_text="Category Choice Code - for example 'GTA2'")
    title = models.CharField(max_length=50,
                        help_text="Category Choice Title - for example 'PhD'")
    pay_per_bu = models.DecimalField(max_digits=8,
                                     decimal_places=2, 
                                     verbose_name="Default pay, "+\
                                                  "per base unit")
    scholarship_per_bu = models.DecimalField(max_digits=8, 
                                             decimal_places=2, 
                                             verbose_name="Scholarship pay, "+\
                                                          "per base unit",)
    bu_lab_bonus = models.DecimalField(max_digits=8,
                                       decimal_places=2, 
                                       verbose_name="Bonus BUs awarded to a "+\
                                                    "course with a lab")

    # ensc-gta2
    def autoslug(self):
        return make_slug(self.account.unit.label + '-' + unicode(self.code))
    slug = AutoSlugField(populate_from=autoslug, 
                         null=False, 
                         editable=False, 
                         unique=True)
    created = models.DateTimeField(default=datetime.datetime.now(), 
                                   editable=False)
    hidden = models.BooleanField(default=False, editable=False)
    config = JSONField(null=False, blank=False, editable=False, default={})

    objects = PassThroughManager.for_queryset_class(TACategoryQuerySet)()
    
    def __unicode__(self):
        return "%s %s %s - %s" % (self.account.unit.label, unicode(self.code), 
                                  unicode(self.title), unicode(self.account))


    @property
    def frozen(self):
        """
        If any of the contracts in this category are SGN or CAN, this
        category can never be changed, only hidden. 
        """
        bools = [contract.frozen for contract in self.contract.all()]
        return True in bools

    def save(self, always_allow=False, *args, **kwargs):
        if not always_allow and self.frozen:
            raise ContractFrozen()
        else:
            super(TACategory, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        if self.frozen:
            raise ContractFrozen()
        else:
            super(TACategory, self).delete(*args, **kwargs)

    def hide(self):
        self.hidden = True
        self.save(always_allow=True)

    def copy_to_new_semester(self, new_hiring_semester):
        cat = TACategory(account=self.account,
                         hiring_semester=new_hiring_semester,
                         code=self.code,
                         title=self.title,
                         pay_per_bu=self.pay_per_bu,
                         scholarship_per_bu=self.scholarship_per_bu,
                         bu_lab_bonus=self.bu_lab_bonus)
        cat.save()
        return cat


class TAContract(models.Model):
    """    
    TA Contract, filled in by TA Administrator
    """
    person = models.ForeignKey(Person)
    category = models.ForeignKey(TACategory, 
                                 related_name="contract")
    status = models.CharField(max_length=4,
                              choices=CONTRACT_STATUS_CHOICES,
                              default="NEW",
                              editable=False)
    sin = models.CharField(max_length=30, 
                           verbose_name="SIN",
                           help_text="Social Insurance Number - 000000000 if unknown")
    deadline_for_acceptance = models.DateField()
    pay_start = models.DateField()
    pay_end = models.DateField()
    payperiods = models.PositiveIntegerField(
                  help_text="During the contract, how many bi-weekly pay periods?")
    appointment = models.CharField(max_length=4, 
                            choices=APPOINTMENT_CHOICES, 
                            default="INIT")
    conditional_appointment = models.BooleanField(default=False)
    tssu_appointment = models.BooleanField(default=True)
    
    # this is really only important if the contract is in Draft status
    # if Signed, the student's acceptance is implied. 
    # if Cancelled, the student's acceptance doesn't matter. 
    accepted_by_student = models.BooleanField(default=False, 
                  help_text="Has the student accepted the contract?")

    comments = models.TextField(blank=True)
    # curtis-lassam-2014-09-01 
    def autoslug(self):
        return make_slug(self.person.first_name + '-' + self.person.last_name \
                            + "-" + unicode(self.pay_start))
    slug = AutoSlugField(populate_from=autoslug, 
                         null=False, 
                         editable=False, 
                         unique=True)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.CharField(max_length=20, null=False, blank=False, \
                                  editable=False)
    config = JSONField(null=False, blank=False, editable=False, default={})
    
    objects = PassThroughManager.for_queryset_class(TAContractQuerySet)()
   
    def __unicode__(self):
        return "%s" % (self.person,)

    @property
    def frozen(self):
        """
        Returns True when this contract is uneditable. 
        """
        return self.status != 'NEW'

    def save(self, always_allow=False, *args, **kwargs):
        if not always_allow and self.frozen:
            raise ContractFrozen()
        else:
            super(TAContract, self).save(*args, **kwargs)
            self.set_grad_student_sin()

    def sign(self):
        """
        Moves the contract from "Draft" to "Contract Signed"
        """
        self.status = 'SGN'
        self.save(always_allow=True)

    def cancel(self):
        """
        Moves the contract from "Contract Signed" to "Cancelled"
        or
        Moves the contract from "New" to *deleted*
        """
        if self.frozen:
            self.status = 'CAN'
            self.save(always_allow=True)
        else:
            self.delete()
    
    def set_grad_student_sin(self):
        """
        Sets the SIN of the GradStudent object, if it exists and hasn't
        already been set. 
        """
        for gs in GradStudent.objects.filter(person=self.person):
            if (('sin' not in gs.config 
                or ('sin' in gs.config and gs.config['sin'] in DUMMY_SINS)) 
                and not self.sin in DUMMY_SINS):
                gs.person.set_sin(self.sin)
                gs.person.save()

    def delete(self, *args, **kwargs):
        if self.frozen:
            raise ContractFrozen()
        else:
            for course in self.course.all():
                course.delete()
            super(TAContract, self).delete(*args, **kwargs)

    def copy(self, created_by):
        """
            Return a copy of this contract, but with status="NEW"
        """
        newcontract = TAContract(person=self.person,
                                 category=self.category,
                                 sin=self.sin,
                                 deadline_for_acceptance= \
                                        self.deadline_for_acceptance,
                                 pay_start=self.pay_start,
                                 pay_end=self.pay_end,
                                 payperiods=self.payperiods,
                                 created_by=created_by,
                                 appointment=self.appointment,
                                 conditional_appointment= \
                                         self.conditional_appointment,
                                 tssu_appointment=self.tssu_appointment,
                                 comments = self.comments)
        newcontract.save()
        for course in self.course.all():
            newcourse = TACourse(course=course.course, 
                                 contract=newcontract,
                                 bu=course.bu, 
                                 labtut=course.labtut)
            newcourse.save()
        return newcontract

    
    @property
    def pay_per_bu(self):
        return self.category.pay_per_bu
    
    @property
    def scholarship_per_bu(self):
        return self.category.scholarship_per_bu

    @property
    def bu_lab_bonus(self):
        return self.category.bu_lab_bonus
    
    @property
    def bu(self):
        if len(self.course.all()) == 0:
            return decimal.Decimal(0)
        else:
            return sum( [course.bu for course in self.course.all()] )

    @property
    def total_bu(self):
        if len(self.course.all()) == 0:
            return decimal.Decimal(0)
        else:
            return sum( [course.total_bu for course in self.course.all()] )
    
    @property
    def total_pay(self):
        if len(self.course.all()) == 0:
            return decimal.Decimal(0)
        else:
            return self.total_bu * self.pay_per_bu

    @property
    def biweekly_pay(self):
        return self.total_pay / self.payperiods

    @property
    def scholarship_pay(self):
        if len(self.course.all()) == 0:
            return decimal.Decimal(0)
        else:
            return self.bu * self.scholarship_per_bu

    @property
    def biweekly_scholarship(self):
        return self.scholarship_pay / self.payperiods

    @property
    def total(self):
        return self.total_pay + self.scholarship_pay

    @property
    def number_of_emails(self):
        return len(self.email_receipt.all())


class TACourse(models.Model):
    course = models.ForeignKey(CourseOffering,
                               blank=False, 
                               null=False,
                               related_name="+")
    contract = models.ForeignKey(TAContract, 
                                 blank=False, 
                                 null=False, 
                                 editable=False,
                                 related_name="course")
    bu = models.DecimalField(max_digits=4, 
                             decimal_places=2,
                             verbose_name="BUs",
                             help_text="The number of Base Units for this course.")
    labtut = models.BooleanField(default=False, 
                                 verbose_name="Lab/Tutorial?", 
                                 help_text="Does this course have a lab or tutorial?")
    def autoslug(self):
        """
        curtis-lassam-2014-09-01 
        """
        return make_slug(self.course.slug)
    slug = AutoSlugField(populate_from=autoslug, 
                         null=False, 
                         editable=False, 
                         unique=False)
    config = JSONField(null=False, blank=False, editable=False, default={})
    
    class Meta:
        unique_together = (('contract', 'course'),)
    
    def __unicode__(self):
        return "Course: %s  TA: %s" % (self.course, self.contract)

    @property
    def frozen(self):
        return self.contract.frozen
    
    def save(self, *args, **kwargs):
        if self.frozen:
            raise ContractFrozen()
        else:
            super(TACourse, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        if self.frozen:
            raise ContractFrozen()
        else:
            super(TACourse, self).delete(*args, **kwargs)

    @property
    def prep_bu(self):
        """
        Return the prep BUs for this assignment
        """
        if self.labtut:
            return self.contract.bu_lab_bonus 
        else:
            return 0

    @property
    def total_bu(self):
        """
        Return the total BUs for this assignment
        """
        return self.bu + self.prep_bu


class EmailReceipt(models.Model):
    contract = models.ForeignKey(TAContract, 
                                 blank=False, 
                                 null=False, 
                                 editable=False,
                                 related_name="email_receipt")
    created = models.DateTimeField(default=datetime.datetime.now(), 
                                   editable=False)
    content = models.TextField(blank=False, null=False)