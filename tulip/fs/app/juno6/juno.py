# juno.py
# Convert juno-106 sysex patches to Amy


import amy
import json
import math
import time

try:
    math.exp2(1)
    def exp2(x):
        return math.exp2(x)
except AttributeError:
    def exp2(x):
        return math.pow(2.0, x)

    # Range is from 10 ms to 12 sec i.e. 1200.
    # (12 sec is allegedly the max decay time of the EG, see
    # page 32 of Juno-106 owner's manual,
    # https://cdn.roland.com/assets/media/pdf/JUNO-106_OM.pdf .)
    # Return int value in ms
    #time = 0.01 * np.exp(np.log(1e3) * midi / 127.0)
    # midi 30 is ~ 200 ms, 50 is ~ 1 sec, so
    #                D=30 
    # 
    # from demo at https://www.synthmania.com/Roland%20Juno-106/Audio/Juno-106%20Factory%20Preset%20Group%20A/14%20Flutes.mp3
    # A11 Brass set                A=3    D=49    S=45 R=32 -> 
    # A14 Flute                        A=23 D=81    S=0    R=18 -> A=200ms, R=200ms, D=0.22 to 0.11 in 0.830 s / 0.28 to 0.14 in 0.92         R = 0.2 to 0.1 in 0.046
    # A16 Brass & Strings    A=44 D=66    S=53 R=44 -> A=355ms, R=                
    # A15 Moving Strings     A=13 D=87             R=35 -> A=100ms, R=600ms,
    # A26 Celeste                    A=0    D=44    S=0    R=81 -> A=2ms                         D=0.48 to 0.24 in 0.340 s                                                     R = 0.9 to 0.5 in 0.1s; R clearly faster than D
    # A27 Elect Piano            A=1    D=85    S=43 R=40 -> A=14ms,    R=300ms
    # A28 Elect. Piano II    A=0    D=68    S=0    R=22 ->                                     D=0.30 to 0.15 in 0.590 s    R same as D?
    # A32 Steel Drums            A=0    D=26    S=0    R=37 ->                                     D=0.54 to 0.27 in 0.073 s
    # A34 Brass III                A=58 D=100 S=94 R=37 -> A=440ms, R=1000ms
    # A35 Fanfare                    A=72 D=104 S=75 R=49 -> A=600ms, R=1200ms 
    # A37 Pizzicato                A=0    D=11    S=0    R=12 -> A=6ms,     R=86ms     D=0.66 to 0.33 in 0.013 s
    # A41 Bass Clarinet        A=11 D=75    S=0    R=25 -> A=92ms,    R=340ms, D=0.20 to 0.10 in 0.820 s /                                                        R = 0.9 to 0.45 in 0.070
    # A42 English Horn         A=8    D=81    S=21 R=16 -> A=68ms,    R=240ms,
    # A45 Koto                         A=0    D=56    S=0    R=39 ->                                     D=0.20 to 0.10 in 0.160 s
    # A46 Dark Pluck             A=0    D=52    S=15 R=63 ->
    # A48 Synth Bass I         A=0    D=34    S=0    R=36 ->                                     D=0.60 to 0.30 in 0.096 s
    # A56 Funky III                A=0    D=24    S=0    R=2                                             D 1/2 in 0.206
    # A61 Piano II                 A=0    D=98    S=0    R=32                                            D 1/2 in 1.200
    # A    0     1     8     11     13     23     44    58
    # ms 6     14    68    92     100    200    355 440
    # D                        11    24    26    34    44    56    68    75    81    98
    # 1/2 time ms    13    206 73    96    340 160 590 830 920 1200
    # R    12    16    18    25     35     37     40
    # ms 86    240 200 340    600    1000 300

# Notes from video https://www.youtube.com/watch?v=zWOs16ccB3M
# A 0 -> 1ms    1.9 -> 30ms    3.1 -> 57ms    3.7 -> 68ms    5.4    -> 244 ms    6.0 -> 323ms    6.3 -> 462ms    6.5 -> 502ms
# D 3.3 -> 750ms

# Addendum: See online emulation
# https://github.com/pendragon-andyh/junox
# based on set of isolated samples
# https://github.com/pendragon-andyh/Juno60

    
def to_attack_time(val):
    """Convert a midi value (0..127) to a time for ADSR."""
    # From regression of sound examples
    return 6 + 8 * val * 127
    # from Arturia video
    #return 12 * exp2(0.066 * midi) - 12

def to_decay_time(val):
    """Convert a midi value (0..127) to a time for ADSR."""
    # time = 12 * np.exp(np.log(120) * midi/100)
    # time is time to decay to 1/2; Amy envelope times are to decay to exp(-3) = 0.05
    # return np.log(0.05) / np.log(0.5) * time
    # from Arturia video
    #return 80 * exp2(0.066 * val * 127) - 80
    return 80 * exp2(0.085 * val * 127) - 80
    

def to_release_time(val):
    """Convert a midi value (0..127) to a time for ADSR."""
    #time = 100 * np.exp(np.log(16) * midi/100)
    #return np.log(0.05) / np.log(0.5) * time
    # from Arturia video
    #return 70 * exp2(0.066 * val * 127) - 70
    return 70 * exp2(0.066 * val * 127) - 70


def to_level(val):
    # Map midi to 0..1, linearly.
    return val


def level_to_amp(level):
    # level is 0.0 to 1.0; amp is 0.001 to 1.0
    if level == 0.0:
        return 0.0
    return float("%.3f" % (0.001 * np.exp(level * np.log(1000.0))))


def to_lfo_freq(val):
    # LFO frequency in Hz varies from 0.5 to 30
    # from Arturia video
    return float("%.3f" % (0.6 * exp2(0.04 * val * 127) - 0.1))


def to_lfo_delay(val):
    """Convert a midi value (0..127) to a time for lfo_delay."""
    #time = 100 * np.exp(np.log(16) * midi/100)
    #return float("%.3f" % (np.log(0.05) / np.log(0.5) * time))
    # from Arturia video
    return float("%.3f" % (18 * exp2(0.066 * val * 127) - 13))


def to_resonance(val):
    # Q goes from 0.5 to 16 exponentially
    return float("%.3f" % (0.7 * exp2(4.0 * val)))


def to_filter_freq(val):
    # filter_freq goes from ? 100 to 6400 Hz with 18 steps/octave
    #return float("%.3f" % (100 * np.exp2(midi / 20.0)))
    # from Arturia video
    #return float("%.3f" % (6.5 * exp2(0.11 * val * 127)))
    #return float("%.3f" % (25 * exp2(0.055 * val * 127)))
    #return float("%.3f" % (25 * exp2(0.083 * val * 127)))
    return float("%.3f" % (13 * exp2(0.0938 * val * 127)))


def ffmt(val):
    """Format float values as max 3 dp, but less if possible."""
    return "%.5g" % float("%.3f" % val)


_PATCHES = None
def get_juno_patch(patch_number):
    # json was created by:
    # import javaobj, json
    # pobj = javaobj.load(open('juno106_factory_patches.ser', 'rb'))
    # patches = [(p.name, list(p.sysex)) for p in pobj.v.elementData if p is not None]
    # with open('juno106patches.json', 'w') as f:
    #     f.write(json.dumps(patches))
    #pobj = javaobj.load(open('juno106_factory_patches.ser', 'rb'))
    #patch = pobj.v.elementData[patch_number]
    global _PATCHES
    if not _PATCHES:
        with open('juno106patches.json', 'r') as f:
            _PATCHES = json.load(f)
    name, sysex = _PATCHES[patch_number]
    return name, bytes(sysex)


class JunoPatch:
    """Encapsulates information in a Juno Patch."""
    name = ""
    lfo_rate = 0
    lfo_delay_time = 0
    dco_lfo = 0
    dco_pwm = 0
    dco_noise = 0
    vcf_freq = 0
    vcf_res = 0
    vcf_env = 0
    vcf_lfo = 0
    vcf_kbd = 0
    vca_level = 0
    env_a = 0
    env_d = 0
    env_s = 0
    env_r = 0
    dco_sub = 0
    stop_16 = False
    stop_8 = False
    stop_4 = False
    pulse = False
    saw = False
    chorus = 0
    pwm_manual = False    # else lfo
    vca_gate = False    # else env
    vcf_neg = False    # else pos
    hpf = 0
    # Map of setup_fn: [params triggering setup]
    post_set_fn = {'lfo': ['lfo_rate', 'lfo_delay_time'],
                                 'dco': ['dco_lfo', 'dco_pwm', 'dco_noise', 'dco_sub', 'stop_16', 'stop_8', 'stop_4',
                                                 'pulse', 'saw', 'pwm_manual', 'vca_level'],
                                 'vcf': ['vcf_neg', 'vcf_env', 'vcf_freq', 'vcf_lfo', 'vcf_res', 'vcf_kbd'],
                                 'env': ['env_a', 'env_d', 'env_s', 'env_r', 'vca_gate'],
                                 'cho': ['chorus', 'hpf']}
    
    # These lists name the fields in the order they appear in the sysex.
    FIELDS = ['lfo_rate', 'lfo_delay_time', 'dco_lfo', 'dco_pwm', 'dco_noise',
                     'vcf_freq', 'vcf_res', 'vcf_env', 'vcf_lfo', 'vcf_kbd', 'vca_level',
                     'env_a', 'env_d', 'env_s', 'env_r', 'dco_sub']
    # After the 16 integer values, there are two bytes of bits.
    BITS1 = ['stop_16', 'stop_8', 'stop_4', 'pulse', 'saw']
    BITS2 = ['pwm_manual', 'vcf_neg', 'vca_gate']

    # Patch number we're based on, if any.
    patch_number = None
    # Name, if any
    name = None
    # Params that have been changed since last send_to_AMY.
    dirty_params = set()
    # Flag to defer param updates.
    defer_param_updates = False
    # Cache for sub-osc freq_coefs.
    sub_freq = '440'
    
    @staticmethod
    def from_patch_number(patch_number):
        name, sysexbytes = get_juno_patch(patch_number)
        return JunoPatch.from_sysex(sysexbytes, name, patch_number)

    @classmethod
    def from_sysex(cls, sysexbytes, name=None, patch_number=None):
        """Decode sysex bytestream into JunoPatch fields."""
        assert len(sysexbytes) == 18
        result = JunoPatch()
        result.name = name
        result.patch_number = patch_number
        result._init_from_sysex(sysexbytes)
        return result

    def _init_from_patch_number(self, patch_number):
        self.patch_number = patch_number
        self.name, sysexbytes = get_juno_patch(patch_number)
        self._init_from_sysex(sysexbytes)
    
    def _init_from_sysex(self, sysexbytes):
        # The first 16 bytes are sliders.
        for index, field in enumerate(self.FIELDS):
            setattr(self, field, int(sysexbytes[index])/127.0)
        # Then there are two bytes of switches.
        for index, field in enumerate(self.BITS1):
            setattr(self, field, (int(sysexbytes[16]) & (1 << index)) > 0)
        # Chorus has a weird mapping.    Bit 5 is ~Chorus, bit 6 is ChorusI-notII
        setattr(self, 'chorus', [2, 0, 1, 0][int(sysexbytes[16]) >> 5])
        for index, field in enumerate(self.BITS2):
            setattr(self, field, (int(sysexbytes[17]) & (1 << index)) > 0)
        # Bits 3 & 4 also have flipped endianness & sense.
        setattr(self, 'hpf', [3, 2, 1, 0][int(sysexbytes[17]) >> 3])

    def __init__(self):
        # TODO: get this from tulip.map
        self.voices = [0,1,2,3]

    def voice_str(self):
        return ",".join([str(x) for x in self.voices])

    def _breakpoint_string(self):
        """Format a breakpoint string from the ADSR parameters reaching a peak."""
        return "%d,%s,%d,%s,%d,0" % (
            to_attack_time(self.env_a), ffmt(1.0), to_attack_time(self.env_a) + to_decay_time(self.env_d),
            ffmt(to_level(self.env_s)), to_release_time(self.env_r)
        )

    def init_AMY(self):
        """Output AMY commands to set up patches on all the allocated voices.
        Send amy.send(voices='0", note=50, vel=1) afterwards."""
        #amy.reset()
        # base_osc is pulse/PWM
        # base_osc + 1 is SAW
        # base_osc + 2 is SUBOCTAVE
        # base_osc + 3 is NOISE
        # base_osc + 4 is LFO
        #     env0 is VCA
        #     env1 is VCF
        self.pwm_osc = 0
        self.saw_osc = 1
        self.sub_osc = 2
        self.nse_osc = 3
        self.lfo_osc = 4
        self.voice_oscs = [
            self.pwm_osc, self.saw_osc, self.sub_osc, self.nse_osc
        ]
        # One-time args to oscs.
        self.amy_send(osc=self.lfo_osc, wave=amy.TRIANGLE, amp='1,0,0,1,0,0')
        osc_setup = {
            'filter_type': amy.FILTER_LPF24, 'mod_source': self.lfo_osc}
        self.amy_send(osc=self.pwm_osc, wave=amy.PULSE, **osc_setup)
        # Setup chained_oscs
        # All the oscs are the same, except:
        #    - only pulse needs duty (but OK if it's cloned, except sub)
        #    - wave is diff for each
        #    - chained osc is diff for each (but not cloned)
        #    - sub has different frequency, no duty
        # So, to update for instance envelope:
        #    - we could run through each osc and update all params
        #    - or just update osc 0, then clone to 1,2,3, then restore
        #        their unique params
        self.amy_send(osc=self.pwm_osc, chained_osc=self.sub_osc)
        self.amy_send(osc=self.sub_osc, chained_osc=self.saw_osc)
        self.amy_send(osc=self.saw_osc, chained_osc=self.nse_osc)
        # Setup all the variable params.
        self.update_lfo()
        self.update_dco()
        self.update_vcf()
        self.update_env()
        self.update_cho()
        self.clone_oscs()

    def _amp_coef_string(self, level):
        return '0,0,%s,1,0,0' % ffmt(max(.001, to_level(level) * to_level(self.vca_level)))

    def _freq_coef_string(self, base_freq):
        return '%s,1,0,0,0,%s,1' % (
            ffmt(base_freq), ffmt(0.03 * to_level(self.dco_lfo)))


    def clone_oscs(self):
        """Having changed params on osc zero, clone to others, then fixup."""
        clone_osc = self.pwm_osc
        self.amy_send(osc=self.saw_osc, clone_osc=clone_osc)
        self.amy_send(osc=self.saw_osc, wave=amy.SAW_UP,
                         amp=self._amp_coef_string(float(self.saw)))
        self.amy_send(osc=self.nse_osc, clone_osc=clone_osc)
        self.amy_send(osc=self.nse_osc, wave=amy.NOISE,
                         amp=self._amp_coef_string(self.dco_noise))
        self.amy_send(osc=self.sub_osc, clone_osc=clone_osc)
        self.amy_send(osc=self.sub_osc, wave=amy.PULSE,
                         amp=self._amp_coef_string(self.dco_sub),
                         freq=self.sub_freq)


    def update_lfo(self):
        lfo_args = {'freq': to_lfo_freq(self.lfo_rate),
                                'bp0': '%i,1.0,%i,1.0,10000,0' % (
                                    to_lfo_delay(self.lfo_delay_time),
                                    to_lfo_delay(self.lfo_delay_time))}
        self.amy_send(osc=self.lfo_osc, **lfo_args)

    def update_dco(self):
        # Only one of stop_{16,8,4} should be set.
        base_freq = 261.63    # The mid note
        if self.stop_16:
            base_freq /= 2
        elif self.stop_4:
            base_freq *= 2

        # PWM square wave.
        const_duty = 0
        lfo_duty = to_level(self.dco_pwm)
        if self.pwm_manual:
            # Swap duty parameters.
            const_duty, lfo_duty = lfo_duty, const_duty
        self.amy_send(
            osc=self.pwm_osc,
            amp=self._amp_coef_string(float(self.pulse)),
            freq=self._freq_coef_string(base_freq),
            duty='%s,0,0,0,0,%s' % (
                ffmt(0.5 + 0.5 * const_duty), ffmt(0.5 * lfo_duty)))
        # Setup the unique freq_coef for the sub_osc.
        self.sub_freq = self._freq_coef_string(base_freq / 2.0)

    def update_vcf(self):
        vcf_env_polarity = -1.0 if self.vcf_neg else 1.0
        self.amy_send(osc=self.pwm_osc, resonance=to_resonance(self.vcf_res),
                                    filter_freq='%s,%s,0,0,%s,%s' % (
                                        ffmt(to_filter_freq(self.vcf_freq)),
                                        ffmt(to_level(self.vcf_kbd)),
                                        ffmt(11 * vcf_env_polarity * to_level(self.vcf_env)),
                                        ffmt(1.25 * to_level(self.vcf_lfo))))

    def update_env(self):
        bp1_coefs = self._breakpoint_string()
        if self.vca_gate:
            bp0_coefs='0,1,0,0'
        else:
            bp0_coefs = self._breakpoint_string()
        self.amy_send(osc=self.pwm_osc, bp0=bp0_coefs, bp1=bp1_coefs)

    def update_cho(self):
        # Chorus & HPF
        eq_l = eq_m = eq_h = 0
        if self.hpf == 0:
            eq_l = 7
            eq_m = -3
            eq_h = -3
        elif self.hpf == 1:
            pass
        elif self.hpf == 2:
            eq_l = -8
        elif self.hpf == 3:
            eq_l = -15
            eq_m = 8
            eq_h = 8
        chorus_args = {
            'eq_l': eq_l, 'eq_m': eq_m, 'eq_h': eq_h,
            'chorus_level': float(self.chorus > 0)
        }
        if self.chorus:
            chorus_args['chorus_depth'] = 0.5
            if self.chorus == 1:
                chorus_args['chorus_freq'] = 0.5
            elif self.chorus == 2:
                chorus_args['chorus_freq'] = 0.83
            elif self.chorus == 3:
                # We choose juno 60-style I+II.    Juno 6-style would be freq=8 depth=0.25
                chorus_args['chorus_freq'] = 1
                chorus_args['chorus_depth'] = 0.08
        #self.amy_send(osc=amy.CHORUS_OSC, **chorus_args)
        # *Don't* repeat for all the notes, these ones are global.
        amy.send(**chorus_args)
        
    # Setters for each Juno UI control
    def set_param(self, param, val):
        setattr(self, param,    val)
        if self.defer_param_updates:
            self.dirty_params.add(param)
        else:
            for group, params in self.post_set_fn.items():
                if param in params:
                    getattr(self, 'update_' + group)()
            self.clone_oscs()

    def send_deferred_params(self):
        for group, params in self.post_set_fn.items():
            if self.dirty_params.intersection(params):
                getattr(self, 'update_' + group)()
        self.clone_oscs()
        self.dirty_params = set()
        self.defer_param_updates = False

    def amy_send(self, osc, **kwargs):
        amy.send(voices=self.voice_str(), osc = osc, **kwargs)

    def set_patch(self, patch):
        self._init_from_patch_number(patch)
        print("New patch", patch, ":", self.name)
        self.init_AMY()

    def set_pitch_bend(self, value):
        amy.send(pitch_bend=value)
