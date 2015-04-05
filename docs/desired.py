server = create_healthcheck_server(port=8080)

# U1
server.add_component(
    name="mail-u1",
    task=TCPCheck(host="1.2.3.4", port=25, timeout=second(10)))

# U2
server.add_component(
    name="mail-u2",
    task=hysteresis(
        task=TCPCheck(host="1.2.3.4", port=25, timeout=second(10)),
        start=fail,
        ok_after=count(5),
        fail_after=count(20)))

# U3
server.add_component(
    name="mail-u3",
    task=hysteresis(
        task=TCPCheck(host="1.2.3.4", port=25, timeout=second(10)),
        start=fail,
        ok_after=minute(1),
        fail_after=minute(2)))

# U4
server.add_component(
    name="mail-u4",
    task=background(
        task=hysteresis(
            task=TCPCheck(host="1.2.3.4", port=25, timeout=second(10)),
            start="FAIL",
            ok_after=minute(1),
            fail_after=minute(2)),
        interval=second(5))

# U5
mail_check = toggle(
    start=ok,
    to_fail=TCPCheck(host="1.2.3.4", port=25, timeout=second(10)),
    to_ok=oneshot(auth=htpasswd_file("/var/lib/healthcheck_users")))

server.add_component(
    name="mail-u5",
    task=mail_check,
    on_post=mail_check.to_ok.fire)

server.run_forever()
