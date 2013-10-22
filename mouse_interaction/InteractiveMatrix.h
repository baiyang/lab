#ifndef INTERACTIVE_MATRIX_H
#define INTERACTIVE_MATRIX_H

#include <QtOpenGL/qgl.h>

class InteractiveMatrix
{
public:
	InteractiveMatrix(void);
	~InteractiveMatrix(void);

	void addTranslation(float x, float y, float z);
	void addRotation(float angle, float x, float y, float z);
	void reset();

	float * getMatrix();
private:
	float _matrix[16];
};

#endif // endif
