from django.shortcuts import render

def settings_error(request):
    return render(request, "settings_error.html")