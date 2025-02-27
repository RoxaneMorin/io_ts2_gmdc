#
#
#



__all__ = ['convert_normal_to_color']



# CONVERSIONS

def convert_normal_to_color(normal: tuple[float, float, float]) -> list[float]:
	return [(f + 1)/2 for f in normal] + [1.0]
