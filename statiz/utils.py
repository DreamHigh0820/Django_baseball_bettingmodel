import re

def parseFloat(value):
	if value is None:
		return 0
	
	str = f"{value}"
	if str[0] == '.':
		str = f"0{str}"
	
	pattern = r"\d+(?:\.\d+)?"
	match = re.search(pattern, str)

	if match:
		float_value = float(match.group())
		return round(float_value, 3)
	else:
		return 0.0

def parseInt(value):
	if value is None:
		return 0

	str = f"{value}"
	pattern = r"\d+"
	match = re.search(pattern, str)

	if match:
		int_value = int(match.group())
		return int_value
	else:
		return 0