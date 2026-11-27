"""Bundle 136 — spdxkit: SPDX license-expression parsing.

Public CLOSED grammar: SPDX Specification v2.3.1, Annex D "SPDX license
expressions" (normative), read 27-11-2026 at
https://spdx.github.io/spdx-spec/v2.3.1/SPDX-license-expressions/ :
operators AND / OR / WITH matched CASE-SENSITIVELY (D.2); ids matched
case-INSENSITIVELY against the list, canonical case is the List's (D.2);
precedence + > WITH > AND > OR, parentheses override (D.4.5); no space
before a '+' suffix and none missing around WITH (D.1). Grammar breaks
are REFUSED BY NAME; unknown ids are JUDGED against the pinned vintage
(verdict UNKNOWN_ID, did-you-mean at distance <= 2) — never guessed.

The id table is the SPDX License List, VINTAGE NAMED in every response:
version 3.29.0, release 2026-09-16T00:00:00Z, 740 license
ids + 86 exception ids + 32 deprecated licenses + 1 deprecated
exceptions. Regenerated from the release tag's licenses.json +
exceptions.json by SCRIPT, never by hand (house rule for closed
tables); table_sha256 is declared in the response and covers exactly
that embedded set (serialization string in the payload).
Same input -> same bytes. No network, no LLM, no float.
"""
import hashlib
import re

__all__ = ["SpdxError", "parse_expression", "LIST_VERSION", "TABLE_SHA256",
           "VERDICT_SET"]

LIST_VERSION = "3.29.0"
LIST_RELEASE_DATE = "2026-09-16"
LIST_SOURCE_URL = "https://spdx.org/licenses/"

# ---------------- closed table (generated, do not edit by hand) ---------
LICENSE_IDS = frozenset((
    '0BSD', '3D-Slicer-1.0', 'AAL', 'ADSL', 'AFL-1.1', 'AFL-1.2', 'AFL-2.0',
    'AFL-2.1', 'AFL-3.0', 'AGPL-1.0', 'AGPL-1.0-only', 'AGPL-1.0-or-later',
    'AGPL-3.0', 'AGPL-3.0-only', 'AGPL-3.0-or-later', 'ALGLIB-Documentation',
    'AMD-newlib', 'AMDPLPA', 'AML', 'AML-glslang', 'AMPAS', 'ANTLR-PD',
    'ANTLR-PD-fallback', 'APAFML', 'APL-1.0', 'APSL-1.0', 'APSL-1.1',
    'APSL-1.2', 'APSL-2.0', 'ASWF-Digital-Assets-1.0',
    'ASWF-Digital-Assets-1.1', 'Abstyles', 'AdaCore-doc', 'Adobe-2006',
    'Adobe-Display-PostScript', 'Adobe-Glyph', 'Adobe-Utopia',
    'Advanced-Cryptics-Dictionary', 'Afmparse', 'Aladdin', 'Apache-1.0',
    'Apache-1.1', 'Apache-2.0', 'App-s2p', 'Arphic-1999', 'Artistic-1.0',
    'Artistic-1.0-Perl', 'Artistic-1.0-cl8', 'Artistic-2.0', 'Artistic-dist',
    'Aspell-RU', 'BOLA-1.1', 'BSD-1-Clause', 'BSD-2-Clause',
    'BSD-2-Clause-Darwin', 'BSD-2-Clause-FreeBSD', 'BSD-2-Clause-NetBSD',
    'BSD-2-Clause-Patent', 'BSD-2-Clause-Views', 'BSD-2-Clause-first-lines',
    'BSD-2-Clause-pkgconf-disclaimer', 'BSD-2-Clause-pos-unchanged',
    'BSD-3-Clause', 'BSD-3-Clause-Attribution', 'BSD-3-Clause-Clear',
    'BSD-3-Clause-HP', 'BSD-3-Clause-LBNL', 'BSD-3-Clause-Modification',
    'BSD-3-Clause-No-Military-License', 'BSD-3-Clause-No-Nuclear-License',
    'BSD-3-Clause-No-Nuclear-License-2014',
    'BSD-3-Clause-No-Nuclear-Warranty', 'BSD-3-Clause-Open-MPI',
    'BSD-3-Clause-OpenWebUI', 'BSD-3-Clause-Sun', 'BSD-3-Clause-Tso',
    'BSD-3-Clause-acpica', 'BSD-3-Clause-flex', 'BSD-4-Clause',
    'BSD-4-Clause-Shortened', 'BSD-4-Clause-UC', 'BSD-4.3RENO',
    'BSD-4.3TAHOE', 'BSD-Advertising-Acknowledgement',
    'BSD-Attribution-HPND-disclaimer', 'BSD-Inferno-Nettverk',
    'BSD-Mark-Modifications', 'BSD-Protection', 'BSD-Source-Code',
    'BSD-Source-Code-no-disclaimer', 'BSD-Source-alt-GPL',
    'BSD-Source-beginning-file', 'BSD-Systemics', 'BSD-Systemics-W3Works',
    'BSD-ask-to-endorse', 'BSL-1.0', 'BUSL-1.1', 'Baekmuk', 'Bahyph', 'Barr',
    'Beerware', 'BitTorrent-1.0', 'BitTorrent-1.1', 'Bitstream-Charter',
    'Bitstream-Vera', 'BlueOak-1.0.0', 'Boehm-GC', 'Boehm-GC-without-fee',
    'Borceux', 'Brian-Gladman-2-Clause', 'Brian-Gladman-3-Clause',
    'Brian-Gladman-3-Clause-no-conversion', 'Buddy', 'Bugroff', 'C-UDA-1.0',
    'CAL-1.0', 'CAL-1.0-Combined-Work-Exception', 'CAPEC-tou', 'CATOSL-1.1',
    'CC-BY-1.0', 'CC-BY-2.0', 'CC-BY-2.5', 'CC-BY-2.5-AU', 'CC-BY-3.0',
    'CC-BY-3.0-AT', 'CC-BY-3.0-AU', 'CC-BY-3.0-DE', 'CC-BY-3.0-IGO',
    'CC-BY-3.0-NL', 'CC-BY-3.0-US', 'CC-BY-4.0', 'CC-BY-NC-1.0',
    'CC-BY-NC-2.0', 'CC-BY-NC-2.5', 'CC-BY-NC-3.0', 'CC-BY-NC-3.0-DE',
    'CC-BY-NC-3.0-IGO', 'CC-BY-NC-4.0', 'CC-BY-NC-ND-1.0', 'CC-BY-NC-ND-2.0',
    'CC-BY-NC-ND-2.5', 'CC-BY-NC-ND-3.0', 'CC-BY-NC-ND-3.0-DE',
    'CC-BY-NC-ND-3.0-IGO', 'CC-BY-NC-ND-4.0', 'CC-BY-NC-SA-1.0',
    'CC-BY-NC-SA-2.0', 'CC-BY-NC-SA-2.0-DE', 'CC-BY-NC-SA-2.0-FR',
    'CC-BY-NC-SA-2.0-UK', 'CC-BY-NC-SA-2.5', 'CC-BY-NC-SA-3.0',
    'CC-BY-NC-SA-3.0-DE', 'CC-BY-NC-SA-3.0-IGO', 'CC-BY-NC-SA-4.0',
    'CC-BY-ND-1.0', 'CC-BY-ND-2.0', 'CC-BY-ND-2.5', 'CC-BY-ND-3.0',
    'CC-BY-ND-3.0-DE', 'CC-BY-ND-4.0', 'CC-BY-SA-1.0', 'CC-BY-SA-2.0',
    'CC-BY-SA-2.0-UK', 'CC-BY-SA-2.1-JP', 'CC-BY-SA-2.5', 'CC-BY-SA-3.0',
    'CC-BY-SA-3.0-AT', 'CC-BY-SA-3.0-DE', 'CC-BY-SA-3.0-IGO', 'CC-BY-SA-4.0',
    'CC-PDDC', 'CC-PDM-1.0', 'CC-SA-1.0', 'CC0-1.0', 'CDDL-1.0', 'CDDL-1.1',
    'CDL-1.0', 'CDLA-Permissive-1.0', 'CDLA-Permissive-2.0',
    'CDLA-Sharing-1.0', 'CECILL-1.0', 'CECILL-1.1', 'CECILL-2.0',
    'CECILL-2.1', 'CECILL-B', 'CECILL-C', 'CERN-OHL-1.1', 'CERN-OHL-1.2',
    'CERN-OHL-P-2.0', 'CERN-OHL-S-2.0', 'CERN-OHL-W-2.0', 'CFITSIO',
    'CMU-Mach', 'CMU-Mach-nodoc', 'CNRI-Jython', 'CNRI-Python',
    'CNRI-Python-GPL-Compatible', 'COIL-1.0', 'CPAL-1.0', 'CPL-1.0',
    'CPOL-1.02', 'CUA-OPL-1.0', 'Caldera', 'Caldera-no-preamble', 'Catharon',
    'ClArtistic', 'Clips', 'Community-Spec-1.0', 'Condor-1.1',
    'Cornell-Lossless-JPEG', 'Cronyx', 'Crossword', 'CryptoSwift',
    'CrystalStacker', 'Cube', 'D-FSL-1.0', 'DEC-3-Clause', 'DL-DE-BY-2.0',
    'DL-DE-ZERO-2.0', 'DOC', 'DRL-1.0', 'DRL-1.1', 'DSDP', 'DocBook-DTD',
    'DocBook-Schema', 'DocBook-Stylesheet', 'DocBook-XML', 'Dotseqn',
    'ECL-1.0', 'ECL-2.0', 'EFL-1.0', 'EFL-2.0', 'EPICS', 'EPL-1.0', 'EPL-2.0',
    'ESA-PL-permissive-2.4', 'ESA-PL-strong-copyleft-2.4',
    'ESA-PL-weak-copyleft-2.4', 'EUDatagrid', 'EUPL-1.0', 'EUPL-1.1',
    'EUPL-1.2', 'Elastic-2.0', 'Entessa', 'ErlPL-1.1', 'Eurosym', 'FBM',
    'FDK-AAC', 'FDK-MPEG-H', 'FSFAP', 'FSFAP-no-warranty-disclaimer', 'FSFUL',
    'FSFULLR', 'FSFULLRSD', 'FSFULLRWD', 'FSL-1.1-ALv2', 'FSL-1.1-MIT', 'FTL',
    'Fair', 'Ferguson-Twofish', 'Frameworx-1.0', 'FreeBSD-DOC', 'FreeImage',
    'Furuseth', 'GCR-docs', 'GD', 'GFDL-1.1', 'GFDL-1.1-invariants-only',
    'GFDL-1.1-invariants-or-later', 'GFDL-1.1-no-invariants-only',
    'GFDL-1.1-no-invariants-or-later', 'GFDL-1.1-only', 'GFDL-1.1-or-later',
    'GFDL-1.2', 'GFDL-1.2-invariants-only', 'GFDL-1.2-invariants-or-later',
    'GFDL-1.2-no-invariants-only', 'GFDL-1.2-no-invariants-or-later',
    'GFDL-1.2-only', 'GFDL-1.2-or-later', 'GFDL-1.3',
    'GFDL-1.3-invariants-only', 'GFDL-1.3-invariants-or-later',
    'GFDL-1.3-no-invariants-only', 'GFDL-1.3-no-invariants-or-later',
    'GFDL-1.3-only', 'GFDL-1.3-or-later', 'GL2PS', 'GLWTPL', 'GPL-1.0',
    'GPL-1.0+', 'GPL-1.0-only', 'GPL-1.0-or-later', 'GPL-2.0', 'GPL-2.0+',
    'GPL-2.0-only', 'GPL-2.0-or-later', 'GPL-2.0-with-GCC-exception',
    'GPL-2.0-with-autoconf-exception', 'GPL-2.0-with-bison-exception',
    'GPL-2.0-with-classpath-exception', 'GPL-2.0-with-font-exception',
    'GPL-3.0', 'GPL-3.0+', 'GPL-3.0-only', 'GPL-3.0-or-later',
    'GPL-3.0-with-GCC-exception', 'GPL-3.0-with-autoconf-exception',
    'Game-Programming-Gems', 'Giftware', 'Glide', 'Glulxe', 'Graphics-Gems',
    'Gutmann', 'HDF5', 'HIDAPI', 'HP-1986', 'HP-1989', 'HPND', 'HPND-DEC',
    'HPND-Fenneberg-Livingston', 'HPND-INRIA-IMAG', 'HPND-Intel',
    'HPND-Kevlin-Henney', 'HPND-MIT-disclaimer', 'HPND-Markus-Kuhn',
    'HPND-Netrek', 'HPND-Pbmplus', 'HPND-SMC', 'HPND-UC', 'HPND-UC-export-US',
    'HPND-doc', 'HPND-doc-sell', 'HPND-export-US',
    'HPND-export-US-acknowledgement', 'HPND-export-US-modify',
    'HPND-export2-US', 'HPND-merchantability-variant',
    'HPND-sell-MIT-disclaimer-xserver', 'HPND-sell-regexpr',
    'HPND-sell-variant', 'HPND-sell-variant-MIT-disclaimer',
    'HPND-sell-variant-MIT-disclaimer-rev',
    'HPND-sell-variant-critical-systems', 'HTMLTIDY', 'HaskellReport',
    'Hippocratic-2.1', 'Hippocratic-3.0-core', 'IBM-pibs', 'ICU',
    'IEC-Code-Components-EULA', 'IJG', 'IJG-short', 'IPA', 'IPL-1.0', 'ISC',
    'ISC-Veillard', 'ISO-permission', 'ImageMagick', 'Imlib2', 'Info-ZIP',
    'Informatica', 'Inner-Net-2.0', 'InnoSetup', 'Intel', 'Intel-ACPI',
    'Interbase-1.0', 'JPL-image', 'JPNIC', 'JSON', 'Jam', 'JasPer-2.0',
    'Kastrup', 'Kazlib', 'Knuth-CTAN', 'LAL-1.2', 'LAL-1.3', 'LGPL-2.0',
    'LGPL-2.0+', 'LGPL-2.0-only', 'LGPL-2.0-or-later', 'LGPL-2.1',
    'LGPL-2.1+', 'LGPL-2.1-only', 'LGPL-2.1-or-later', 'LGPL-3.0',
    'LGPL-3.0+', 'LGPL-3.0-only', 'LGPL-3.0-or-later', 'LGPLLR', 'LOOP',
    'LPD-document', 'LPL-1.0', 'LPL-1.02', 'LPPL-1.0', 'LPPL-1.1', 'LPPL-1.2',
    'LPPL-1.3a', 'LPPL-1.3c', 'LZMA-SDK-9.11-to-9.20', 'LZMA-SDK-9.22',
    'Latex2e', 'Latex2e-translated-notice', 'Leptonica', 'LiLiQ-P-1.1',
    'LiLiQ-R-1.1', 'LiLiQ-Rplus-1.1', 'Libpng', 'Linux-OpenIB',
    'Linux-man-pages-1-para', 'Linux-man-pages-copyleft',
    'Linux-man-pages-copyleft-2-para', 'Linux-man-pages-copyleft-var',
    'Lucida-Bitmap-Fonts', 'MIPS', 'MIT', 'MIT-0', 'MIT-CMU', 'MIT-Click',
    'MIT-Festival', 'MIT-Khronos-old', 'MIT-Modern-Variant', 'MIT-STK',
    'MIT-Wu', 'MIT-advertising', 'MIT-enna', 'MIT-feh', 'MIT-open-group',
    'MIT-testregex', 'MITNFA', 'MMIXware', 'MMPL-1.0.1', 'MPEG-SSG',
    'MPL-1.0', 'MPL-1.1', 'MPL-2.0', 'MPL-2.0-no-copyleft-exception',
    'MS-LPL', 'MS-PL', 'MS-RL', 'MTLL', 'MVT-1.1', 'Mackerras-3-Clause',
    'Mackerras-3-Clause-acknowledgment', 'MakeIndex', 'Martin-Birgmeier',
    'McPhee-slideshow', 'Minpack', 'MirOS', 'Motosoto', 'MulanPSL-1.0',
    'MulanPSL-2.0', 'Multics', 'Mup', 'NAIST-2003', 'NASA-1.3', 'NBPL-1.0',
    'NCBI-PD', 'NCGL-UK-2.0', 'NCL', 'NCSA', 'NGPL', 'NICTA-1.0', 'NIST-PD',
    'NIST-PD-TNT', 'NIST-PD-fallback', 'NIST-Software', 'NLOD-1.0',
    'NLOD-2.0', 'NLPL', 'NOSL', 'NPL-1.0', 'NPL-1.1', 'NPOSL-3.0', 'NRL',
    'NTIA-PD', 'NTP', 'NTP-0', 'Naumen', 'Net-SNMP', 'NetCDF', 'Newsletr',
    'Nokia', 'Noweb', 'Nunit', 'O-UDA-1.0', 'OAR', 'OCCT-PL', 'OCLC-2.0',
    'ODC-By-1.0', 'ODbL-1.0', 'OFFIS', 'OFL-1.0', 'OFL-1.0-RFN',
    'OFL-1.0-no-RFN', 'OFL-1.1', 'OFL-1.1-RFN', 'OFL-1.1-no-RFN', 'OGC-1.0',
    'OGDL-Taiwan-1.0', 'OGL-Canada-2.0', 'OGL-UK-1.0', 'OGL-UK-2.0',
    'OGL-UK-3.0', 'OGTSL', 'OLDAP-1.1', 'OLDAP-1.2', 'OLDAP-1.3', 'OLDAP-1.4',
    'OLDAP-2.0', 'OLDAP-2.0.1', 'OLDAP-2.1', 'OLDAP-2.2', 'OLDAP-2.2.1',
    'OLDAP-2.2.2', 'OLDAP-2.3', 'OLDAP-2.4', 'OLDAP-2.5', 'OLDAP-2.6',
    'OLDAP-2.7', 'OLDAP-2.8', 'OLFL-1.3', 'OML', 'OPL-1.0', 'OPL-UK-3.0',
    'OPUBL-1.0', 'OSC-1.0', 'OSET-PL-2.1', 'OSL-1.0', 'OSL-1.1', 'OSL-2.0',
    'OSL-2.1', 'OSL-3.0', 'OSSP', 'OpenMDW-1.0', 'OpenPBS-2.3', 'OpenSSL',
    'OpenSSL-standalone', 'OpenVision', 'PADL', 'PDDL-1.0', 'PHP-3.0',
    'PHP-3.01', 'PPL', 'PSF-2.0', 'ParaType-Free-Font-1.3', 'Parity-6.0.0',
    'Parity-7.0.0', 'Pixar', 'Plexus', 'PolyForm-Noncommercial-1.0.0',
    'PolyForm-Small-Business-1.0.0', 'PostgreSQL', 'Python-2.0',
    'Python-2.0.1', 'QPL-1.0', 'QPL-1.0-INRIA-2004', 'Qhull', 'RHeCos-1.1',
    'RPL-1.1', 'RPL-1.5', 'RPSL-1.0', 'RSA-MD', 'RSCPL', 'Rdisc', 'Ruby',
    'Ruby-pty', 'SAX-PD', 'SAX-PD-2.0', 'SCEA', 'SGI-B-1.0', 'SGI-B-1.1',
    'SGI-B-2.0', 'SGI-OpenGL', 'SGMLUG-PM', 'SGP4', 'SHL-0.5', 'SHL-0.51',
    'SISSL', 'SISSL-1.2', 'SL', 'SMAIL-GPL', 'SMLNJ', 'SMPPL', 'SNIA', 'SOFA',
    'SPL-1.0', 'SSH-OpenSSH', 'SSH-short', 'SSLeay-standalone', 'SSPL-1.0',
    'SUL-1.0', 'SWL', 'Saxpath', 'SchemeReport', 'Sendmail', 'Sendmail-8.23',
    'Sendmail-Open-Source-1.1', 'SimPL-2.0', 'Sleepycat', 'Soundex',
    'Spencer-86', 'Spencer-94', 'Spencer-99', 'StandardML-NJ',
    'SugarCRM-1.1.3', 'Sun-PPP', 'Sun-PPP-2000', 'SunPro', 'Symlinks',
    'TAPR-OHL-1.0', 'TCL', 'TCP-wrappers', 'TGPPL-1.0', 'TMate', 'TORQUE-1.1',
    'TOSL', 'TPDL', 'TPL-1.0', 'TTWL', 'TTYP0', 'TU-Berlin-1.0',
    'TU-Berlin-2.0', 'TekHVC', 'TermReadKey', 'ThirdEye', 'TrustedQSL',
    'UCAR', 'UCL-1.0', 'UMich-Merit', 'UPL-1.0', 'URT-RLE', 'Ubuntu-font-1.0',
    'UnRAR', 'Unicode-3.0', 'Unicode-DFS-2015', 'Unicode-DFS-2016',
    'Unicode-TOU', 'UnixCrypt', 'Unlicense', 'Unlicense-libtelnet',
    'Unlicense-libwhirlpool', 'VOSTROM', 'VSL-1.0', 'Vim', 'Vixie-Cron',
    'W3C', 'W3C-19980720', 'W3C-20150513', 'WTFNMFPL', 'WTFPL', 'Watcom-1.0',
    'Widget-Workshop', 'WordNet', 'Wsuipa', 'X11',
    'X11-distribute-modifications-variant', 'X11-no-permit-persons',
    'X11-swapped', 'XFree86-1.1', 'XSkat', 'Xdebug-1.03', 'Xerox', 'Xfig',
    'Xnet', 'YPL-1.0', 'YPL-1.1', 'ZPL-1.1', 'ZPL-2.0', 'ZPL-2.1', 'Zed',
    'Zeeff', 'Zend-2.0', 'Zimbra-1.3', 'Zimbra-1.4', 'Zlib', 'any-OSI',
    'any-OSI-perl-modules', 'atc-game', 'bcrypt-Solar-Designer', 'blessing',
    'bzip2-1.0.5', 'bzip2-1.0.6', 'check-cvs', 'checkmk',
    'copyleft-next-0.3.0', 'copyleft-next-0.3.1', 'curl', 'cve-tou',
    'diffmark', 'dtoa', 'dvipdfm', 'eCos-2.0', 'eGenix', 'etalab-2.0', 'fwlw',
    'gSOAP-1.3b', 'generic-xts', 'gnuplot', 'gtkbook', 'hdparm',
    'hyphen-bulgarian', 'iMatix', 'jove', 'libpng-1.6.35', 'libpng-2.0',
    'libselinux-1.0', 'libtiff', 'libutil-David-Nugent', 'lsof', 'magaz',
    'mailprio', 'man2html', 'metamail', 'mpi-permissive', 'mpich2', 'mplus',
    'ngrep', 'pkgconf', 'pnmstitch', 'psfrag', 'psutils', 'python-ldap',
    'radvd', 'snprintf', 'softSurfer', 'ssh-keyscan', 'swrule',
    'threeparttable', 'ulem', 'w3m', 'wwl', 'wxWindows', 'xinetd',
    'xkeyboard-config-Zinoviev', 'xlock', 'xpp', 'xzoom',
    'zlib-acknowledgement',
))

EXCEPTION_IDS = frozenset((
    '389-exception', 'Asterisk-exception',
    'Asterisk-linking-protocols-exception', 'Autoconf-exception-2.0',
    'Autoconf-exception-3.0', 'Autoconf-exception-generic',
    'Autoconf-exception-generic-3.0', 'Autoconf-exception-macro',
    'Bison-exception-1.24', 'Bison-exception-2.2', 'Bootloader-exception',
    'CGAL-linking-exception', 'CLISP-exception-2.0',
    'Classpath-exception-2.0', 'Classpath-exception-2.0-short',
    'DigiRule-FOSS-exception', 'Digia-Qt-LGPL-exception-1.1',
    'FLTK-exception', 'Fawkes-Runtime-exception', 'Font-exception-2.0',
    'GCC-exception-2.0', 'GCC-exception-2.0-note', 'GCC-exception-3.1',
    'GNAT-exception', 'GNOME-examples-exception', 'GNU-compiler-exception',
    'GPL-3.0-389-ds-base-exception', 'GPL-3.0-interface-exception',
    'GPL-3.0-linking-exception', 'GPL-3.0-linking-source-exception',
    'GPL-CC-1.0', 'GStreamer-exception-2005', 'GStreamer-exception-2008',
    'Gmsh-exception', 'Google-Patent-WebM', 'Independent-modules-exception',
    'KiCad-libraries-exception', 'LGPL-3.0-linking-exception', 'LLGPL',
    'LLVM-exception', 'LZMA-exception', 'Libtool-exception',
    'Linux-syscall-note', 'Nokia-Qt-exception-1.1', 'OCCT-exception-1.0',
    'OCaml-LGPL-linking-exception', 'OpenJDK-assembly-exception-1.0',
    'PCRE2-exception', 'PS-or-PDF-font-exception-20170817',
    'QPL-1.0-INRIA-2004-exception', 'Qt-GPL-exception-1.0',
    'Qt-LGPL-exception-1.1', 'Qwt-exception-1.0',
    'RRDtool-FLOSS-exception-2.0', 'SANE-exception', 'SHL-2.0', 'SHL-2.1',
    'SWI-exception', 'Simple-Library-Usage-exception',
    'Spelling-Provider-LGPL-exception', 'Swift-exception',
    'Texinfo-exception', 'UBDL-exception', 'Universal-FOSS-exception-1.0',
    'WxWindows-exception-3.1', 'cryptsetup-OpenSSL-exception',
    'eCos-exception-2.0', 'erlang-otp-linking-exception', 'fmt-exception',
    'freertos-exception-2.0', 'gnu-javamail-exception', 'harbour-exception',
    'i2p-gpl-java-exception', 'kvirc-openssl-exception',
    'libpri-OpenH323-exception', 'mif-exception', 'mxml-exception',
    'openvpn-openssl-exception', 'polyparse-exception', 'romic-exception',
    'rsync-linking-exception', 'sqlitestudio-OpenSSL-exception',
    'stunnel-exception', 'u-boot-exception-2.0', 'vsftpd-openssl-exception',
    'x11vnc-openssl-exception',
))

DEPRECATED_LICENSES = frozenset((
    'AGPL-1.0', 'AGPL-3.0', 'BSD-2-Clause-FreeBSD', 'BSD-2-Clause-NetBSD',
    'GFDL-1.1', 'GFDL-1.2', 'GFDL-1.3', 'GPL-1.0', 'GPL-1.0+', 'GPL-2.0',
    'GPL-2.0+', 'GPL-2.0-with-GCC-exception',
    'GPL-2.0-with-autoconf-exception', 'GPL-2.0-with-bison-exception',
    'GPL-2.0-with-classpath-exception', 'GPL-2.0-with-font-exception',
    'GPL-3.0', 'GPL-3.0+', 'GPL-3.0-with-GCC-exception',
    'GPL-3.0-with-autoconf-exception', 'LGPL-2.0', 'LGPL-2.0+', 'LGPL-2.1',
    'LGPL-2.1+', 'LGPL-3.0', 'LGPL-3.0+', 'Net-SNMP', 'Nunit',
    'StandardML-NJ', 'bzip2-1.0.5', 'eCos-2.0', 'wxWindows',
))

DEPRECATED_EXCEPTIONS = frozenset((
    'Nokia-Qt-exception-1.1',
))

TABLE_SHA256 = hashlib.sha256(
    ("\n".join(sorted(LICENSE_IDS)) + "\n"
     + "\n".join(sorted(EXCEPTION_IDS)) + "\n"
     + "\n".join(sorted(DEPRECATED_LICENSES)) + "\n"
     + "\n".join(sorted(DEPRECATED_EXCEPTIONS))).encode("utf-8")
).hexdigest()

# --- the parser (tail of spdxkit.py; the table constants live above) ----

# Annex D.3 / D.4 grammar, recursive descent:
#   expression := or_expr
#   or_expr    := and_expr ( "OR" and_expr )*
#   and_expr   := with_expr ( "AND" with_expr )*
#   with_expr  := primary ( "WITH" exception-id )?
#   primary    := "(" or_expr ")" | simple-id
# Precedence + > WITH > AND > OR (Annex D.4.5) falls out of the nesting.

MAX_EXPR_CHARS = 1000        # named cap, refused by reason
_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.\-:]*")
_DOCREF_RE = re.compile(
    r"DocumentRef-[A-Za-z0-9.\-]+:LicenseRef-[A-Za-z0-9.\-]+$")
_LOWER_OPS = {"and": "AND", "or": "OR", "with": "WITH"}

VERDICT_SET = ["BAD_EXCEPTION_SLOT", "CASE_MISMATCH", "DEPRECATED_ID",
               "OK", "UNKNOWN_ID", "USER_REF"]


class SpdxError(Exception):
    """Named refusal. .field is 'expression' or 'list_version';
    .reason is a token from the refusal set named in the tests."""

    def __init__(self, reason, message, expected=None, field="expression"):
        self.reason = reason
        self.field = field
        self.message = message
        self.expected = expected
        super().__init__(message)


def _fail(reason, message, expected=None, field="expression"):
    raise SpdxError(reason, message, expected, field)


# lower-case index of the closed table (Annex D.2: ids match case-
# insensitively, the List's case is canonical). Built once at import.
def _build_index():
    idx = {}
    for canon in LICENSE_IDS:
        idx[canon.lower()] = (canon, "license")
    for canon in EXCEPTION_IDS:
        idx.setdefault(canon.lower(), (canon, "exception"))
    return idx


_INDEX = _build_index()
_ALL_IDS = tuple(sorted(LICENSE_IDS | EXCEPTION_IDS))


def _nearest(token, max_dist=2):
    """did-you-mean at a NAMED distance (precedent: agent_modelid)."""
    def lev(a, b):
        if abs(len(a) - len(b)) > max_dist:
            return max_dist + 1
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            cur = [i]
            for j, cb in enumerate(b, 1):
                cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                               prev[j - 1] + (ca != cb)))
            prev = cur
        return prev[len(b)]
    hits = []
    for cand in _ALL_IDS:
        if lev(token.lower(), cand.lower()) <= max_dist:
            hits.append(cand)
    return sorted(hits)[:5]


def _classify(token):
    """-> dict describing the term against the pinned vintage."""
    plus = token.endswith("+")
    base = token[:-1] if plus else token
    if ":" in base and not _DOCREF_RE.fullmatch(base):
        _fail("colon_id_deprecated",
              "'%s': a trailing (or stray) ':' is the deprecated SPDX-1.x "
              "'or later' colon — write the canonical '-or-later' id, a "
              "'+' suffix, or the DocumentRef-<id>:LicenseRef-<id> form "
              "of Annex D.3" % token,
              expected="e.g. GPL-2.0-or-later, GPL-2.0+, or "
                       "DocumentRef-spdx-tool-1.2:LicenseRef-MIT-Style-2")
    if base.startswith("LicenseRef-") or base.startswith("DocumentRef-"):
        if base.startswith("LicenseRef-"):
            rest = base[len("LicenseRef-"):]
            if not rest or not re.fullmatch(r"[A-Za-z0-9.\-]+", rest):
                _fail("invalid_identifier",
                      "'%s' is not a LicenseRef: the reference part must "
                      "be one or more of [A-Za-z0-9.-] (Annex D.3)"
                      % token)
        return {"kind": "user_ref", "in_list": True,
                "canonical_case": True, "canonical_id": token,
                "deprecated": False, "plus": False}
    hit = _INDEX.get(base.lower())
    if hit:
        canon, kind = hit
        return {"kind": kind, "in_list": True,
                "canonical_case": canon == base,
                "canonical_id": canon + ("+" if plus else ""),
                "deprecated": (canon in DEPRECATED_LICENSES
                               or canon in DEPRECATED_EXCEPTIONS),
                "plus": plus}
    return {"kind": "unknown", "in_list": False, "canonical_case": False,
            "canonical_id": None, "deprecated": False, "plus": plus,
            "nearest": _nearest(base)}


def _tokenize(expr):
    toks = []
    i, n = 0, len(expr)
    while i < n:
        c = expr[i]
        if c == " ":
            i += 1
            continue
        if c == "(":
            toks.append(("LPAREN", c, i))
            i += 1
            continue
        if c == ")":
            toks.append(("RPAREN", c, i))
            i += 1
            continue
        m = _ID_RE.match(expr, i)
        if not m:
            _fail("invalid_character",
                  "character %r at offset %d is neither an id character "
                  "nor an operator nor a parenthesis (Annex D)" % (c, i),
                  expected="ids [A-Za-z0-9][A-Za-z0-9.-]* ; AND OR WITH ; "
                           "( )")
        word = m.group(0)
        pos = i
        i = m.end()
        if word in ("AND", "OR", "WITH"):
            toks.append(("OP", word, pos))
            continue
        if word.lower() in _LOWER_OPS:
            _fail("operator_case",
                  "'%s' at offset %d is not an operator: AND, OR and WITH "
                  "are matched case-sensitively (Annex D.2) — write '%s'"
                  % (word, pos, _LOWER_OPS[word.lower()]),
                  expected="AND | OR | WITH (uppercase)")
        if i < n and expr[i] == "+":      # no space before '+' (Annex D.1)
            word += "+"
            i += 1
        if word.endswith("+") and i < n and expr[i] == "+":
            _fail("invalid_identifier",
                  "'%s' at offset %d: only ONE trailing '+' is the "
                  "short-form suffix (Annex D.3)" % (word + "+", pos))
        toks.append(("ID", word, pos))
    return toks


class _Parser:
    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def take(self):
        t = self.peek()
        if t is None:
            _fail("unexpected_end",
                  "the expression ends where a term was expected "
                  "(Annex D.4)")
        self.i += 1
        return t

    def parse(self):
        node = self.or_expr()
        t = self.peek()
        if t is not None:
            if t[0] == "RPAREN":
                _fail("unbalanced_paren",
                      "a ')' at offset %d has no opening (Annex D.4.1)"
                      % t[2])
            _fail("missing_operator",
                  "'%s' at offset %d follows a term with no AND/OR/WITH "
                  "between (Annex D.4)" % (t[1], t[2]),
                  expected="AND | OR | WITH, or the end of the expression")
        return node

    def or_expr(self):
        parts = [self.and_expr()]
        while True:
            t = self.peek()
            if t and t[0] == "OP" and t[1] == "OR":
                self.i += 1
                parts.append(self.and_expr())
            else:
                break
        return {"op": "OR", "children": parts} if len(parts) > 1 else parts[0]

    def and_expr(self):
        parts = [self.with_expr()]
        while True:
            t = self.peek()
            if t and t[0] == "OP" and t[1] == "AND":
                self.i += 1
                parts.append(self.with_expr())
            else:
                break
        return {"op": "AND", "children": parts} if len(parts) > 1 else parts[0]

    def with_expr(self):
        left = self.primary()
        t = self.peek()
        if t and t[0] == "OP" and t[1] == "WITH":
            self.i += 1
            et = self.take()
            if et[0] != "ID":
                _fail("with_operand_not_id",
                      "WITH at offset %d must be followed by a license-"
                      "exception-id (Annex D.4.4)" % t[2],
                      expected="an exception id, e.g. "
                               "Classpath-exception-2.0")
            if et[1].endswith("+"):
                _fail("plus_on_exception_slot",
                      "'%s' at offset %d: the '+' suffix is defined for "
                      "license ids, not for the WITH operand (Annex D.3, "
                      "D.4.4)" % (et[1], et[2]))
            if isinstance(left, dict) and "op" in left:
                _fail("with_operand_compound",
                      "WITH at offset %d takes a SIMPLE expression on the "
                      "left (Annex D.4.4); parenthesize to say what you "
                      "mean" % t[2])
            leaf = _term(et[1], et[2], slot="with_right")
            return {"op": "WITH", "children": [left, leaf]}
        return left

    def primary(self):
        t = self.take()
        if t[0] == "LPAREN":
            node = self.or_expr()
            c = self.peek()
            if c is None:
                _fail("unbalanced_paren",
                      "the '(' at offset %d is never closed (Annex D.4.1)"
                      % t[2])
            if c[0] != "RPAREN":
                _fail("missing_operator",
                      "expected ')' after the group opened at offset %d, "
                      "found '%s' at offset %d" % (t[2], c[1], c[2]))
            self.i += 1
            return node
        if t[0] == "RPAREN":
            _fail("unbalanced_paren",
                  "a ')' at offset %d has no opening (Annex D.4.1)" % t[2])
        if t[0] == "OP":
            _fail("operator_without_operand",
                  "operator '%s' at offset %d has no term before it "
                  "(Annex D.4)" % (t[1], t[2]))
        w, pos = t[1], t[2]
        if w in ("NONE", "NOASSERTION"):
            _fail("special_value_not_expression",
                  "'%s' at offset %d is a tag VALUE of the SPDX document "
                  "(PackageLicense* clauses), not a token of the Annex D "
                  "expression grammar" % (w, pos),
                  expected="ids AND/OR/WITH over ids or LicenseRef-...")
        return _term(w, pos, slot="term")


def _term(token, pos, slot):
    info = _classify(token)
    node = {"id": token, "kind": info["kind"], "in_list": info["in_list"],
            "canonical_case": info["canonical_case"],
            "canonical_id": info["canonical_id"],
            "deprecated": info["deprecated"], "plus": info["plus"],
            "position": pos}
    if "nearest" in info:
        node["nearest"] = info["nearest"]
    flags = []
    if not info["in_list"]:
        flags.append("UNKNOWN_ID")
    if slot == "with_right" and info["kind"] != "exception":
        flags.append("BAD_EXCEPTION_SLOT")
    if slot == "term" and info["kind"] == "exception":
        flags.append("BAD_EXCEPTION_SLOT")
    node["flags"] = flags
    return node


def _canonical(node):
    """Flat canonical string; parentheses only where precedence needs
    them (OR under AND)."""
    if "id" in node:
        return node["id"]
    if node["op"] == "WITH":
        return "%s WITH %s" % (_canonical(node["children"][0]),
                               node["children"][1]["id"])
    parts = []
    for ch in node["children"]:
        s = _canonical(ch)
        if "op" in ch and ch["op"] != node["op"] and ch["op"] == "OR":
            s = "(" + s + ")"
        parts.append(s)
    return (" %s " % node["op"]).join(parts)


def _collect(node, acc, in_with_right=False):
    if "id" in node:
        acc.append(dict(node, with_slot=in_with_right))
        return
    if node["op"] == "WITH":
        _collect(node["children"][0], acc)
        _collect(node["children"][1], acc, in_with_right=True)
        return
    for ch in node["children"]:
        _collect(ch, acc)


def parse_expression(expression, list_version=None):
    """One SPDX license expression -> tree, per-term verdicts against
    the PINNED vintage, canonical string. Grammar breaks are refused
    by name; unknown ids are JUDGED (verdict UNKNOWN_ID + did-you-mean
    at distance <= 2), never guessed."""
    applied_defaults = []
    if list_version is None:
        list_version = LIST_VERSION
        applied_defaults.append(
            "list_version=%s (the only embedded vintage; a closed table "
            "is named, never assumed)" % LIST_VERSION)
    if list_version != LIST_VERSION:
        _fail("list_version",
              "list_version '%s' is not the embedded vintage: this build "
              "carries the SPDX License List %s (release %s) only — ids "
              "are never scored against a table the tool does not hold"
              % (list_version, LIST_VERSION, LIST_RELEASE_DATE),
              expected=LIST_VERSION, field="list_version")
    if not isinstance(expression, str) or not expression.strip():
        _fail("empty_expression", "the expression is empty (Annex D)")
    if len(expression) > MAX_EXPR_CHARS:
        _fail("expression_too_long",
              "expression is %d characters; the named cap is %d"
              % (len(expression), MAX_EXPR_CHARS))
    if "  " in expression or expression != expression.strip():
        _fail("whitespace", "double spaces and surrounding spaces are "
                            "refused by name (Annex D: single-spaced "
                            "tokens)")
    toks = _tokenize(expression)
    if not toks:
        _fail("empty_expression", "the expression is empty (Annex D)")
    node = _Parser(toks).parse()

    terms = []
    _collect(node, terms)
    verdicts = set()
    for t in terms:
        for f in t["flags"]:
            verdicts.add(f)
        if t["kind"] == "user_ref":
            verdicts.add("USER_REF")
        if t["in_list"] and not t["canonical_case"]:
            verdicts.add("CASE_MISMATCH")
        if t["deprecated"]:
            verdicts.add("DEPRECATED_ID")
    if not verdicts:
        verdicts.add("OK")

    out = {
        "expression": expression,
        "list_version": list_version,
        "list_source": LIST_SOURCE_URL,
        "list_release_date": LIST_RELEASE_DATE,
        "table": {
            "licenses": len(LICENSE_IDS),
            "exceptions": len(EXCEPTION_IDS),
            "deprecated_licenses": len(DEPRECATED_LICENSES),
            "deprecated_exceptions": len(DEPRECATED_EXCEPTIONS),
            "serialization": ("sha256 over UTF-8 of: sorted license ids "
                              "joined by \\n, then exception ids, then "
                              "deprecated licenses, then deprecated "
                              "exceptions (each joined by \\n, sections "
                              "joined by \\n)"),
            "sha256": TABLE_SHA256,
        },
        "tree": node,
        "terms": terms,
        "verdicts": sorted(verdicts),
        "verdict_set": VERDICT_SET,
        "canonical": _canonical(node),
        "grammar": "SPDX spec v2.3.1 Annex D — AND OR WITH, precedence "
                   "+ > WITH > AND > OR, parentheses override",
        "max_expression_chars": MAX_EXPR_CHARS,
    }
    if applied_defaults:
        out["applied_defaults"] = applied_defaults
    return out
