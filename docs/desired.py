server = create_healthcheck_server(port=8080)

# U1
server.add_component(
    name="mail-u1",
    task=check_tcp_service(host="1.2.3.4", port=25, timeout=second(10)))

# U2
server.add_component(
    name="mail-u2",
    task=hysteresis(
        task=check_tcp_service(host="1.2.3.4", port=25, timeout=second(10)),
        start=fail,
        ok_after="5 times",
        fail_after="20 times"))

# U3
server.add_component(
    name="mail-u3",
    task=hysteresis(
        task=check_tcp_service(host="1.2.3.4", port=25, timeout="10 seconds"),
        start=fail,
        ok_after=minute(1),
        fail_after="2 minutes"))

# U4
mail_check = periodic(
    task=hysteresis(
        task=check_tcp_service(host="1.2.3.4", port=25,
                                      timeout="10 seconds"),
        start="FAIL",
        ok_after="1 minute",
        fail_after="2 minutes"),
    interval="5 seconds")
server.add_component(
    name="mail-u4",
    task=mail_check.get_state)

# U5
mail_check = toggle(
    start="OK",
    to_fail=check_tcp_service(host="1.2.3.4", port=25, timeout="10 seconds"),
    to_ok=oneshot(basic_auth=htpasswd_file("/var/lib/healthcheck_users")))

server.add_component(
    name="mail-u5",
    task=mail_check.get_state,
    on_post=mail_check.to_ok.fire)

server.run()
