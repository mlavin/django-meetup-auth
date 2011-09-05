from django.http import HttpResponseNotFound, HttpResponseServerError
from django.test import TestCase


def test_404(request):
    return HttpResponseNotFound()


def test_500(request):
    return HttpResponseServerError()
