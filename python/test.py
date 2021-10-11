import proaudio_remote as p8
import time

class TestCallbacks(p8.RemoteCallbacks):
    def on_connected(self, remote):
        print("connected to: " + str(remote))

    def on_zone_updated(self, zone):
        print("zone updated: " + repr(zone))

def test(remote):
    zone = remote.outputs_digital[1]
    #eq_values = [150,140,128,128,128]
    #eq_values = [140,135,128,128,135]
    #zone.set_eq(eq_values)
    #zone.set_eq_flat()
    #zone.bass = 145
    #zone.treble = 135
    #zone.switch = AudioZoneAnalogIn(3)
    print(str(zone.dump()))

cbs = TestCallbacks()
remote = p8.Remote("proaudio.p8.dmb.opdenkamp.eu", callbacks=cbs)
while not remote.connected:
    time.sleep(1)
test(remote)
time.sleep(10)
