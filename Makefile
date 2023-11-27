# Compiler and flags
PYTHON = python3
RM = rm -f

# Target executable
TARGET = bchoc

# Source file
SOURCE = bhoc.py

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(PYTHON) -m py_compile bchoc.py
	mv $(SOURCE)$(PYC_EXT) bchoc
	chmod +x bchoc

clean:
	$(RM) $(TARGET)
