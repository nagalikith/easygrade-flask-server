import random
import import_helper as ih
#used to generate hex code

#default length of hex code
config = {"length": ih.get_env_val("HEX_ID_LENGTH")}

hex_chars = "0123456789abcdef"

def gen_hex(length=None):
  if (type(length) != int or length <= 0):
    length = config["length"]

  res  = ''

  for i in range(length):
    res += hex_chars[random.randint(0, 15)]

  return(res)

def check_hex(val, length=None):
  if (len(val) != length):
    return False

  for char in val:
    if (val not in hex_chars):
      return False

  return True
