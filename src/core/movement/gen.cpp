#include <bits/stdc++.h>
using namespace std;
int main(){
    vector<string> ls {"forward","back","right","left","attack","attack2"};
    ofstream cfout("setinfo.cfg",ios::out|ios::binary);
    for(auto s:ls){
        cfout<<format("setinfo \"{}\" 0\n",s);
        for(auto N:{-1,1,-999}){
            ofstream fout(format("{}{}.cfg",s,N),ios::out|ios::binary);
            fout<<format("toggle \"{}\" \"{} 0 0\"\n",s,N);
            fout.close();
            
            cfout<<format("alias f_{}{} \"exec Horizon/src/core/movement/{}{}.cfg\"\n",s,N,s,N);
        }
        cfout<<'\n';
    }

    return 0;
}