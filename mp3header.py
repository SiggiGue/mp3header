# -- coding: utf-8 --
"""
This module implements a solution to read the header information of mp3 files.
Additionally an estimate for the length of the mp3 files is implemented.

Examples
--------

import mp3header


# the parse() function is very simple it just returns
# the content of the header as follows:

header = mp3header.parse('Test.mp3')
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


Author: Siegfried Gündert

"""
import os
from json import dumps

# the length of the mp3 header is 4 bytes
num_bytes_mp3_header = 4

# list of header element names and the
# number of bits reserved for the element
element_bits = [
    ('Sync', 11),
    ('Version', 2),
    ('Layer', 2),
    ('ErrorProtection', 1),
    ('BitRate', 4),
    ('SampleRate', 2),
    ('Padding', 1),
    ('Private', 1),
    ('ChannelMode', 2),
    ('ModeExtension', 2),
    ('Copyright', 1),
    ('Original', 1),
    ('Emphasis', 2),
]

# each header element covers a possible range of integers
# some elements are dependent on other elements of the header.
# For example the element 'SampleRate' depends on the  element
# 'Version'. This data structure is implemented in the
# following dictionary:
element_description = {
    'Sync': {
        2047: True
    },
    'Version': {
        0: 'MPEG 2.5',
        1: None,
        2: 'MPEG 2',
        3: 'MPEG 1',
    },
    'Layer': {
        0: None,
        1: 'Layer III',
        2: 'Layer II',
        3: 'Layer I',
    },
    'ErrorProtection': {
 	0: '16-Bit CRC nach dem Header',
        1: 'keine CRC',
    },
    'BitRate': {
        'Version': {
            'MPEG 1': {
                'Layer': {
                    'Layer I': {
                        1: 32, 2: 64, 3: 96, 4: 128, 5: 160, 6: 192, 7: 224, 8: 256,
                        9: 288, 10: 320, 11: 352, 12: 384, 13: 416, 14: 448,
                    },
                    'Layer II': {
                        1: 32, 2: 48, 3: 56, 4: 64, 5: 80, 6: 96, 7: 112, 8: 128,
                        9: 160, 10: 192, 11: 224, 12: 256, 13: 320, 14: 384,
                    },
                    'Layer III': {
                        1: 32, 2: 40, 3: 48, 4: 56, 5: 64, 6: 80, 7: 96, 8: 112,
                        9: 128, 10: 160, 11: 192, 12: 224, 13: 256, 14: 320,
                    },
                },
            },
            'MPEG 2': {
                'Layer': {
                    'Layer I': {
                        1: 32, 2: 48, 3: 56, 4: 64, 5: 80, 6: 96, 7: 112, 8: 128,
                        9: 144, 10: 160, 11: 176, 12: 192, 13: 224, 14: 256,
                    },
                    'Layer II': {
                        1: 8, 2: 16, 3: 24, 4: 32, 5: 40, 6: 48, 7: 56, 8: 64,
                        9: 80, 10: 96, 11: 112, 12: 128, 13: 144, 14: 160,
                    },
                },
            },
            'MPEG 2.5': {
                'Layer': {
                    'Layer I': {
                        1: 32, 2: 48, 3: 56, 4: 64, 5: 80, 6: 96, 7: 112, 8: 128,
                        9: 144, 10: 160, 11: 176, 12: 192, 13: 224, 14: 256,
                    },
                    'Layer II': {
                        1: 8, 2: 16, 3: 24, 4: 32, 5: 40, 6: 48, 7: 56, 8: 64,
                        9: 80, 10: 96, 11: 112, 12: 128, 13: 144, 14: 160,
                    },
                },
            },
        },
    },
    'SampleRate': {
        'Version': {
            'MPEG 1': {
                0: 44100,
                1: 48000,
                2: 32000,
            },
            'MPEG 2': {
                0: 22050,
                1: 24000,
                2: 16000,
            },
            'MPEG 2.5': {
                0: 11025,
                1: 12000,
                2: 8000,
            },
        },
    },
    'Padding': {
        0: 'Frame will not be filled up',
        1: 'Frame will be filled with extra slot',
    },
    'Private': {
        0: False,
        1: True
    },
    'ChannelMode': {
        0: (2, 'Stereo'),
        1: (2, 'Joint Stereo'),
        2: (2, '2 Mono Kanäle'),
        3: (1, 'Mono'),
    },
    'ModeExtension': { # TODO
        'Layer': {
            'Layer I': {
                0: 'Subbands 4 to 31',
                1: 'Subbands 8 to 31',
                2: 'Subbands 12 to 31',
                3: 'Subbands 16 to 31',
            },
            'Layer II': {
                0: 'Subbands 4 to 31',
                1: 'Subbands 8 to 31',
                2: 'Subbands 12 to 31',
                3: 'Subbands 16 to 31',
            },
            'Layer III': {
                0: 'Intensity-Stereo: off; M/S-Stereo: off',
                1: 'Intensity-Stereo: on; M/S-Stereo: off',
                2: 'Intensity-Stereo: off; M/S-Stereo: on',
                3: 'Intensity-Stereo: on; M/S-Stereo: on',
            },
        },
    },
    'Copyright': {
        0: False,
        1: True
    },
    'Original': {
        0: False,
        1: True,
    },
    'Emphasis': {
        0: 'no emphasis',
        1: '50/15 ms',
        2: 'reserved',
        3: 'ITU-T J.17',
    },
}


def _parse_header_bytes_as_bitstr(path, num_bytes=num_bytes_mp3_header):
    """ Returns a string containing zeros and ones
    the function parses the first num_bytes from the file specified by <path>.
    the string has 8*num_bytes digits

    Parameters
    ----------
    path : string, containing path to a mp3-file
    num_bytes : number of bytes to parse from the beginning of the file

    Returns
    -------
    header_bytes_bit_string : string with zeros an ones denoting the bits
    """

    header_bytes_bit_string = list()
    with open(path, 'rb') as f:
        for i in range(num_bytes):
            byte = f.read(1)
            byte = ord(byte)
            byte = bin(byte)[2:].rjust(8, '0')
            header_bytes_bit_string.append(byte)
    return ''.join(header_bytes_bit_string)


def _get_header_values_dict_from_header_bytes(header_bytes_bit_string,
                                              element_bits=element_bits):
    """ Returns a dict bith integer values from n bits defined by
    the list element_bits= [('key', nbits), ('',...)]

    Parameters
    ----------
    header_bytes_bit_string : string with zeros an ones denoting the bits
    element_bits : list of header element names and the
        number of bits reserved for the element (example: [('Elmnt1', 4), ...])

    Returns
    -------
    header_values_dict : dictionary, keys are the elements and values are
        integers of the bits
    """

    header_values_dict = dict()
    start = 0
    for element, bits in element_bits:
        end = start + bits
        header_values_dict[element] = int(header_bytes_bit_string[start:end], 2)
        start = end
    return header_values_dict


def _get_description_from_header_values_dict(header_values_dict,
                                             element_description=element_description):
    """ Returns a dictionary containing the descriptions of the header values
    mapped by <element_description>.
    This function performs something like a hierarchical mapping of key-value pairs.
    It turns the integer values in the <header_values_dict>
    to the according descriptions. For example the specifications
    of mp3 files.

    Parameters
    ----------
    header_values_dict : dictionary, keys are the header elements and values are
        integers of the bits

    element_description : dictionary, keys are header element names and the
        values are possible descriptions for given integer values. See the
        strucure of mp3header.element_description and the corresponding docstring

    Returns
    -------
    header_describtions_dict : dictionary, keys are the elements of the header and
        and values are the descriptions for the specific integer value
        given by header_values_dict.
    """

    def get_description_recursive(description, value):
        if any(description):
            if all([type(key) is int for key in description.keys()]):
                return description[value]
            elif all([type(key) is str for key in description.keys()]):
                element = list(description.keys())[0]
                description = description[element][element_description[element][header_values_dict[element]]]
                header_description = get_description_recursive(description, value)
                return header_description
        return None

    header_describtions_dict = dict()

    for element, value in header_values_dict.items():
        description = element_description[element]
        header_describtions_dict[element] = get_description_recursive(description, value)

    return header_describtions_dict


def parse(path):
    """ Returns mp3 header information as dictionary.

    Parameters
    ----------
    path : string, containing the path to an mp3-file

    Returns
    -------
    header_descriptionsd : dictionary, keys
    """
    header_bitstr = _parse_header_bytes_as_bitstr(path)
    header_valuesd = _get_header_values_dict_from_header_bytes(header_bitstr)
    header_descriptionsd = _get_description_from_header_values_dict(header_valuesd)
    return header_descriptionsd


class Mp3Info:
    """
    Return an object providing
    header information about a specified mp3-file
    and an estimate about the length in seconds.

    Parameters
    ----------
    path : string, containing the path to an mp3-file

    Returns
    -------
    obj: Mp3Info object

    Examples
    --------
    mp3i = Mp3Info('Test.mp3')
    print(mp3i.len_sec)
    print(mp3i.header)

    """
    def __init__(self, path):
        self._path = path
        self._bits_per_byte = 8

        self._header_bitstr = _parse_header_bytes_as_bitstr(
            self._path)

        self._header_valuesd = _get_header_values_dict_from_header_bytes(
            self._header_bitstr)

        if not self._header_valuesd['Sync']==2047:
            raise(IOError("""The header from '{}' is not in sync
            with the mp3 header specifications. It seems not
            to be a mp3-file.""".format(self._path))
            )

        self._header_descriptionsd = _get_description_from_header_values_dict(
            self._header_valuesd)

    def __repr__(self):
        return dumps(self.header, indent=4)

    @property
    def header(self):
        """ Returns header information as dictionary """
        return dict(self._header_descriptionsd)

    @property
    def header_valuesd(self):
        """ Returns the header as dictionary, keys are
        the elements and values are integers
        """
        return dict(self._header_valuesd)

    @property
    def header_bitstr(self):
        """ Returns the header as bit string """
        return dict(self._header_bitstr)

    @property
    def bit_rate(self):
        """ Returns bit rate in kbyte/s """
        return self._header_descriptionsd['BitRate']

    @property
    def sample_rate(self):
        """ Returns sample rate in hertz """
        return self._header_descriptionsd['SampleRate']

    @property
    def channels(self):
        """ Returns the number of channels """
        return self._header_descriptionsd['ChannelMode'][0]

    @property
    def mode(self):
        """ Returns the mode of the mp3-file (Stereo, Mono, Joint Stereo) """
        return self._header_descriptionsd['ChannelMode'][1]

    @property
    def size(self):
        """ Returns the file size in byte """
        return os.path.getsize(self._path)

    @property
    def len_sec(self):
        """ Returns the mp3-file length in seconds """
        return 1e-3 * self.size * self._bits_per_byte / self.bit_rate
