# Compiler and flags
PYTHON = python3
RM = rm -f

# Target executable
TARGET = bchoc

# Source file
SOURCE = bhoc.py

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(PYTHON) -m py_compile $(SOURCE)
	mv $(SOURCE)$(PYC_EXT) $(TARGET)
	chmod +x $(TARGET)

clean:
	$(RM) $(TARGET)
