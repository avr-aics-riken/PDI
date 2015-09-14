from distutils.core import setup
import py2exe

setup(
	console=['pdi.py', 'xpdi_genparam.py', 'xpdi_moea_cheetah.py', 'ffvc_eval_2Dcyl.py']
	)

