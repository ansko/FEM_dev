# FEM jon main folder

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

# 

https://stackoverflow.com/questions/5542910

    cd path/to/submodule
    git add <stuff>
    git commit -m "comment"
    git push
***

    cd /main/project
    git add path/to/submodule
    git commit -m "updated my submodule"
    git push
