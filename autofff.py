from argparse import ArgumentParser
import logging
import os.path
import sys

import scanner

if __name__ == "__main__":
	logging.basicConfig(level=logging.DEBUG)

	logger = logging.getLogger(__name__)

	parser = ArgumentParser()
	parser.add_argument('header', type=str, help="Path of c-header file to generate fff-fakes for.")
	parser.add_argument('-i', '--includes', type=str, help="Additional directory to be included for compilation. These are passed down as '-I' includes to the compiler.", required=False, action='append')
	parser.add_argument('-f', '--fakes', type=str, help="Path of the fake libc and additional include directories that you would like to include before the normal '-I' includes.", required=True, action='append')
	parser.add_argument('-d', '--defines', type=str, help="Define/macro to be passed to the preprocessor.", required=False, action='append')

	args = parser.parse_args()

	logger.debug(f"Provided cmd-args: {', '.join(sys.argv[1:])}")

	filename, fileext = os.path.splitext(args.header)
	if fileext != '.h':
		logger.warning(f"Detected non-standard header file extension '{fileext}' (expected '.h'-file).")

	scanner = scanner.GCCScanner(targetHeader=args.header, fakes=args.fakes, includes=args.includes, defines=args.defines)

	scanner.scan_included_headers()
	functions = scanner.scan_function_declarations()
	logger.info(f"Function declarations found: {', '.join( [ f.name for f in functions ])}")
