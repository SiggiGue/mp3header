mp3header
=========

This module implements a solution to read the header information of mp3 files. Additionally an estimate for the length of the mp3 files is implemented.

Examples
--------
```python
import mp3header


# the read() function is very simple it just returns
# the content of the header as follows:

header = mp3header.read('Test.mp3')
header
>>> {'BitRate': 128,
 'ChannelMode': (2, 'Stereo'),
 'Copyright': False,
 'Emphasis': 'no emphasis',
 'ErrorProtection': 'keine CRC',
 'Layer': 'Layer III',
 'ModeExtension': None,
 'Original': True,
 'Padding': 'Frame wird nicht aufgef\xc3\xbcllt',
 'Private': False,
 'SampleRate': 44100,
 'Sync': True,
 'Version': 'MPEG 1'}
 
# a bit fancier: object oriented with estimate of the length in sec
# use the Mp3Info() object:

mp3info = mp3header.Mp3Info('Test.mp3')
mp3info.header
mp3info.len_sec
```
