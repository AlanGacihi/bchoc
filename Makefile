# Compiler and flags
PYTHON = python3
RM = rm -f

# Target executable
TARGET = bchoc

# Source file
SOURCE = bhoc.py

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(PYTHON) -m pyinstaller --onefile $(SOURCE)
	mv dist/$(SOURCE:py=) $(TARGET)

clean:
	$(RM) -r dist $(TARGET) __pycache__ *.spec
