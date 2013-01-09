编译成DLL文件：

g++ -c -DBUILDING_EXPORT_DLL selection.cpp
g++ -shared -o selection.dll selection.o
