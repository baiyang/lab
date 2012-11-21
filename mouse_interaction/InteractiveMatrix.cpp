#include "InteractiveMatrix.h"


InteractiveMatrix::InteractiveMatrix(void)
{
	this->reset();
}


InteractiveMatrix::~InteractiveMatrix(void)
{
}

void InteractiveMatrix::reset()
{
	glMatrixMode(GL_MODELVIEW);

	glPushMatrix();
		glLoadIdentity();
		glGetFloatv(GL_MODELVIEW_MATRIX, this->_matrix);


	glPopMatrix();
}

void InteractiveMatrix::addRotation( float angle, float x, float y, float z )
{
	glPushMatrix();
		glLoadIdentity();
		glRotatef(angle, x, y, z);
		glMultMatrixf(this->_matrix);
		glGetFloatv(GL_MODELVIEW_MATRIX, this->_matrix);
	glPopMatrix();
}

void InteractiveMatrix::addTranslation( float x, float y, float z )
{
	glPushMatrix();
		glLoadIdentity();
		glTranslatef(x, y, z);
		glMultMatrixf(this->_matrix);
		glGetFloatv(GL_MODELVIEW_MATRIX, this->_matrix);
	glPopMatrix();
}

float * InteractiveMatrix::getMatrix()
{
	return this->_matrix;
}


