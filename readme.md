# FEM job main folder

I. Submodules  
git submodule add https://github.com/ansko/RELEASE_CppPolygons.git RELEASE_CppPolygons  
git submodule add https://github.com/ansko/ClusterRunner.git cluster  
II. Preparatoin  
cd RELEASE_CppPolygons
cmake CMakeLists.txt
make


# Settings

FEMFolder - folder where FEM executables are placed


# Running

./proc.py
./main.py (i wann remove it later)


# Some useful information

## https://stackoverflow.com/questions/5542910 (commiting submodule)

    cd path/to/submodule
    git add <stuff>
    git commit -m "comment"
    git push

    cd /main/project
    git add path/to/submodule
    git commit -m "updated my submodule"
    git push
