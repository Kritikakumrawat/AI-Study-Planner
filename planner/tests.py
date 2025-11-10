from django.test import TestCase, Client
from django.urls import reverse
from .models import Subject, Notes
from django.core.files.base import ContentFile
import json

class GenerateNotesTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.subject_no_syllabus = Subject.objects.create(name='Test Subject No Syllabus')
        self.subject_with_syllabus = Subject.objects.create(name='Test Subject With Syllabus')
        # Create a dummy syllabus file
        self.subject_with_syllabus.syllabus_file.save('test_syllabus.pdf', ContentFile(b'PDF content'))

    def test_generate_notes_no_syllabus_ajax(self):
        """Test AJAX request for subject without syllabus"""
        url = reverse('generate_notes', args=[self.subject_no_syllabus.id])
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('No syllabus available', data['message'])

    def test_generate_notes_no_syllabus_non_ajax(self):
        """Test non-AJAX request for subject without syllabus"""
        url = reverse('generate_notes', args=[self.subject_no_syllabus.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('notes', args=[self.subject_no_syllabus.id]))

    def test_generate_notes_with_syllabus_ajax(self):
        """Test AJAX request for subject with syllabus"""
        url = reverse('generate_notes', args=[self.subject_with_syllabus.id])
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('note', data)
        # Check if note was created
        self.assertTrue(Notes.objects.filter(subject=self.subject_with_syllabus, ai_generated=True).exists())

    def test_generate_notes_with_syllabus_non_ajax(self):
        """Test non-AJAX request for subject with syllabus"""
        url = reverse('generate_notes', args=[self.subject_with_syllabus.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('notes', args=[self.subject_with_syllabus.id]))
        # Check if note was created
        self.assertTrue(Notes.objects.filter(subject=self.subject_with_syllabus, ai_generated=True).exists())

    def tearDown(self):
        self.subject_no_syllabus.delete()
        self.subject_with_syllabus.delete()
