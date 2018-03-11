def includeme(config):
    config.add_static_view('static', '/static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('signup','/signup')
    config.add_route('verify_email','/verify')
    config.add_route('login','/login')
    config.add_route('signout','/signout')
    config.add_route('send_totp', '/send-otp')
    config.add_route('check_totp','/check-otp')
