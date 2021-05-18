from django.test import TestCase
from django.urls import reverse
from courselib.testing import basic_page_tests
from discuss.models import DiscussionTopic, DiscussionMessage
from coredata.models import CourseOffering, Member
from courselib.testing import TEST_COURSE_SLUG, Client
import random


class SimpleTest(TestCase):
    fixtures = ['basedata', 'coredata']

    def setUp(self):
        self.offering = CourseOffering.objects.get(slug=TEST_COURSE_SLUG)
        self.offering.set_discussion(True)
        self.offering.save()
        members = Member.objects.filter(offering=self.offering).exclude(role='DROP').exclude(role='TA').exclude(person__userid__isnull=True)
        members = list(members)
        
        # create a bunch of discussion
        for i in range(25):
            t = DiscussionTopic(offering=self.offering, title='Topic '+str(i), content='Content '+str(i),
                                author=random.choice(members))
            t.save()
            m = DiscussionMessage(topic=t, content='**Content** A'+str(i), author=random.choice(members))
            m.save()
            m = DiscussionMessage(topic=t, content='//Content// B'+str(i), author=random.choice(members))
            m.save()
        
        self.topic = t
        self.message = m
    
    def test_page_load(self):
        """
        Tests that various pages load
        """
        # as instructor...
        client = Client()
        client.login_user("ggbaker")

        url = reverse('offering:discussion:discussion_index', kwargs={'course_slug': self.offering.slug})
        response = basic_page_tests(self, client, url)
        self.assertEqual(response.status_code, 200)
        
        url = reverse('offering:discussion:create_topic', kwargs={'course_slug': self.offering.slug})
        response = basic_page_tests(self, client, url)
        self.assertEqual(response.status_code, 200)

        url = reverse('offering:discussion:view_topic', kwargs={'course_slug': self.offering.slug, 'topic_slug': self.topic.slug})
        response = basic_page_tests(self, client, url)
        self.assertEqual(response.status_code, 200)

        url = reverse('offering:discussion:change_topic_status', kwargs={'course_slug': self.offering.slug, 'topic_slug': self.topic.slug})
        response = basic_page_tests(self, client, url)
        self.assertEqual(response.status_code, 200)

        url = reverse('offering:discussion:download', kwargs={'course_slug': self.offering.slug})
        response = basic_page_tests(self, client, url, check_valid=False)
        self.assertEqual(response.status_code, 200)

        # as the author of the topic/message
        client = Client()
        client.login_user(self.topic.author.person.userid)

        url = reverse('offering:discussion:edit_topic', kwargs={'course_slug': self.offering.slug, 'topic_slug': self.topic.slug})
        response = basic_page_tests(self, client, url)
        self.assertEqual(response.status_code, 200)

        client = Client()
        client.login_user(self.message.author.person.userid)
        
        url = reverse('offering:discussion:edit_message', kwargs={'course_slug': self.offering.slug,
                      'topic_slug': self.topic.slug, 'message_slug': self.message.slug})
        response = basic_page_tests(self, client, url)
        self.assertEqual(response.status_code, 200)
        
        url = reverse('offering:discussion:remove_message', kwargs={'course_slug': self.offering.slug,
                      'topic_slug': self.topic.slug, 'message_slug': self.message.slug})
        response = client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(DiscussionMessage.objects.get(id=self.message.id).status, 'HID')

        #  Make sure students can't download the json dump of discussions:
        member = Member.objects.filter(offering=self.offering, role='STUD').exclude(person__userid__isnull=True).first()
        client = Client()
        client.login_user(member.person.userid)
        url = reverse('offering:discussion:download', kwargs={'course_slug': self.offering.slug})
        response = client.get(url)
        self.assertEqual(response.status_code, 403)
