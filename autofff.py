from argparse import ArgumentParser
import logging
import os.path
import sys

import scanner
import generator

if __name__ == "__main__":
	parser = ArgumentParser()
	parser.add_argument('header',
		type=str, 
		help="Path of c-header file to generate fff-fakes for.")
	parser.add_argument('-O', '--output',
		type=str,
		help="Output file for the generated fake header",
		required=True)
	parser.add_argument('-I', '--include',
		type=str,
		help="Additional directory to be included for compilation. These are passed down as '-I' includes to the compiler.",
		required=False,
		action='append',
		dest='includes')
	parser.add_argument('-i', '--includefile',
		type=str,
		help="File to be included for compilation. These are passed down as '-include' includes to the compiler.",
		required=False,
		action='append',
		dest='includeFiles')
	parser.add_argument('-F', '--fake',
		type=str,
		help="Path of the fake libc and additional include directories that you would like to include before the normal '-I' includes.",
		required=True,
		action='append',
		dest='fakes')
	parser.add_argument('-D', '--define',
		type=str,
		help="Define/macro to be passed to the preprocessor.",
		required=False,
		action='append',
		dest='defines')
	parser.add_argument('--debug',
		help="Print various types of debugging information.",
		action='store_const',
		dest='logLevel',
		const=logging.DEBUG,
		default=logging.WARNING,
		required=False)
	parser.add_argument('--verbose',
		help="Increase output verbosity",
		action='store_const',
		dest='logLevel',
		const=logging.INFO)
	args = parser.parse_args()

	logging.basicConfig(level=args.logLevel)
	logger = logging.getLogger(__name__)

	logger.debug(f"Provided cmd-args: {', '.join(sys.argv[1:])}.")

	filename, fileext = os.path.splitext(args.header)
	if fileext != '.h':
		logger.warning(f"Detected non-standard header file extension '{fileext}' (expected '.h'-file).")

	scnr = scanner.GCCScanner(
		targetHeader=args.header,
		fakes=args.fakes,
		includes=args.includes,
		includeFiles=args.includeFiles,
		defines=args.defines)

	result = scnr.scan()
	logger.info(f"Function declarations found: {', '.join( [ f.name for f in result.declarations ])}.")
	logger.info(f"Function definitions found: {', '.join( [ f.decl.name for f in result.definitions ])}.")

	gen = generator.SimpleFakeGenerator(
		os.path.splitext(os.path.basename(args.output))[0],
		args.header,
		args.includeFiles)

	outputFile = args.output.strip()
	if not os.path.exists(os.path.dirname(outputFile)):
		dirname = os.path.dirname(outputFile)
		os.makedirs(dirname)
		logger.debug(f"New directory for output file created {dirname}.")

	logger.info(f"Generatring output file {outputFile}...")
	with open(outputFile, "w") as fs:
		gen.generate(result, fs)

	logger.info(f"Generation complete!")
