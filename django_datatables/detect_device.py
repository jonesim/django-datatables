
def detect_device(request):
    if 'android' in request.META['HTTP_USER_AGENT'].lower() or 'iphone' in request.META['HTTP_USER_AGENT'].lower():
        return {'mobile':True}
    return {'mobile': False}
