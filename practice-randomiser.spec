# -*- mode: python -*-

block_cipher = None


a = Analysis(['practice-randomiser.py'],
             pathex=['C:\\Users\\col52j\\Documents\\Code\\practice-randomiser'],
             binaries=[],
             datas=[],
             hiddenimports = ['pandas._libs.tslibs.timedeltas',
                'pandas._libs.tslibs.nattype',
                'pandas._libs.tslibs.np_datetime',
                'pandas._libs.skiplist'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='practice-randomiser',
          debug=False,
          strip=False,
          upx=False,
          runtime_tmpdir=None,
          console=True )
