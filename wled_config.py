seg_start = 0
seg_stop = 100

# how to get name of fx index list(requests.get('http://wled-wled.fritz.box/json/effects').json())[60] -> 'Scanner Dual'
wled_pattern_json = {
    'red': {
        'on': True,
        'mainseg': 0,  # SM
        'seg': [
            {
                'id': 0,
                'start': seg_start,
                'stop': seg_stop,
                'grp': 1,
                'spc': 0,
                'col': [
                    [255, 0, 0],
                    [0, 0, 0],
                    [0, 0, 0],
                ],
                'on': True,
                'bri': 255,
                'fx': 60,  # effect fx
                'sx': 203,  # fx speed
                'ix': 246,
                'transition': 5,
            }
        ]
    },
    'green': {
        'on': True,
        'mainseg': 0,  # SM
        'seg': [
            {
                'id': 0,
                'start': seg_start,
                'stop': seg_stop,
                'grp': 1,
                'spc': 0,
                'col': [
                    [0, 255, 0],
                    [0, 255, 0],
                    [0, 255, 0],
                ],
                'on': True,
                'bri': 255,
                'fx': 0,  # effect fx
                'ix': 255,
                'transition': 5,
            }
        ]
    },
    'off': {
        'on': True,
        'seg': [
            {
                'id': 0,
                'on': False,
                'transition': 5,
            }
        ]


    },
    'white': {
        'on': True,
        'mainseg': 0,  # SM
        'seg': [
            {
                'id': 0,
                'start': seg_start,
                'stop': seg_stop,
                'grp': 1,
                'spc': 0,
                'col': [
                    [255, 255, 255],
                    [255, 255, 255],
                    [0, 0, 0],
                ],
                'on': True,
                'bri': 255,
                'fx': 60,  # effect fx
                'sx': 64,  # fx speed
                'ix': 113,
                'transition': 5,
            }
        ]
    },
    'spot': {
        'on': True,
        'mainseg': 0,  # SM
        'seg': [
            {
                'id': 0,
                'start': seg_start,
                'stop': seg_stop,
                'grp': 2,
                'spc': 4,
                'col': [
                    [255, 255, 255],
                    [255, 255, 255],
                    [255, 255, 255],
                ],
                'on': True,
                'bri': 255,
                'fx': 0,
                'transition': 5,
            },
        ]
    },
    'dim': {
        'on': True,
        'mainseg': 0,  # SM
        'seg': [
            {
                'id': 0,
                'on': True,
                'bri': 32,
                'transition': 5,
            },
        ]
    }
}
