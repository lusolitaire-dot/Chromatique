#include <time.h>
// Chromatique's fully learned evaluator for the isolated Stockfish-19 fork.
// GPL-3.0-or-later. Stockfish NNUE evaluation is never called.
#include "chromatique_eval.h"
#include "misc.h"
#include "uci.h"
#ifdef __APPLE__
#include <mach-o/dyld.h>
#endif
#include "movegen.h"
#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <unordered_map>
namespace Stockfish::Chromatique {
namespace {
constexpr int N=820,H=512,K=32,P=1968;
struct Model {std::array<float,H*K> w2t{};std::vector<float> data,policyEncoder;std::unordered_map<std::string,int> moves;std::string sha,path;unsigned generation=0;};
Model net;
std::filesystem::path executable_directory;
[[noreturn]] void fail(const std::string& message){std::cerr<<"Chromatique model error: "<<message<<std::endl;std::exit(1);}
constexpr int O_B1=N*H,O_W2=O_B1+H,O_B2=O_W2+H*K,O_VALUE=O_B2+K,O_VBIAS=O_VALUE+K,O_LINEAR=O_VBIAS+1,O_LBIAS=O_LINEAR+N,O_POLICY=O_LBIAS+1,O_PBIAS=O_POLICY+H*P,O_TEMP=O_PBIAS+P,COUNT=O_TEMP+1;
void first_layer_reference(const std::array<float,N>& x,std::array<float,H>& h,float& direct){
    const float* w=net.data.data();for(int j=0;j<H;++j)h[j]=w[O_B1+j];direct=w[O_LBIAS];
    for(int i=0;i<N;++i)if(x[i]!=0){float v=x[i];direct+=w[O_LINEAR+i]*v;const float* column=w+i*H;for(int j=0;j<H;++j)h[j]+=column[j]*v;}
    for(float& v:h)v=std::max(0.0f,v);
}
float dot(const float* w,const float* h){float a=0,b=0,c=0,d=0;for(int i=0;i<H;i+=4){a+=w[i]*h[i];b+=w[i+1]*h[i+1];c+=w[i+2]*h[i+2];d+=w[i+3]*h[i+3];}return (a+b)+(c+d);}
}
// Standalone packaging, 2026-11-16: locate the bundled model independently of GUI working directory.
void initialize_executable_path(const std::filesystem::path& input){
    namespace fs=std::filesystem;fs::path executable=input;std::error_code error;
#ifdef __APPLE__
    std::uint32_t size=0;_NSGetExecutablePath(nullptr,&size);std::vector<char> buffer(size);
    if(_NSGetExecutablePath(buffer.data(),&size)==0)executable=buffer.data();
#elif defined(__linux__)
    auto actual=fs::read_symlink("/proc/self/exe",error);if(!error)executable=actual;
#elif defined(_WIN32)
    executable=CommandLine::get_binary_directory(input)/input.filename();
#endif
    error.clear();auto canonical=fs::weakly_canonical(executable,error);
    executable_directory=(error?fs::absolute(executable):canonical).parent_path();
}
std::string default_path(){
    if(const char* p=std::getenv("CHROMATIQUE_NATIVE_MODEL");p&&*p)return p;
    auto model=executable_directory.parent_path()/"weights"/"chromatique-v4.1.0.native";
    auto adjacent=executable_directory/"weights"/"chromatique-v4.1.0.native";
    if(std::filesystem::is_regular_file(adjacent))model=adjacent;
    auto utf8=model.u8string();return std::string(utf8.begin(),utf8.end());
}
void load(const std::filesystem::path& path){
    std::ifstream f(path,std::ios::binary);if(!f)fail("cannot open "+path.string());
    char magic[8],sha[64];std::uint32_t dims[4];std::uint64_t expected;
    f.read(magic,8);f.read(reinterpret_cast<char*>(dims),16);f.read(sha,64);f.read(reinterpret_cast<char*>(&expected),8);
    bool separate=bool(f)&&!std::memcmp(magic,"CHROMA4\0",8);
    if(!f||(!separate&&std::memcmp(magic,"CHROMA3\0",8))||dims[0]!=N||dims[1]!=H||dims[2]!=K||dims[3]!=P)fail("incompatible header");
    std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(f)),{});
    const int extra=separate?N*H+H:0;
    if(bytes.size()!=(COUNT+extra)*sizeof(float)+P*6)fail("truncated/trailing model data");
    std::uint64_t checksum=14695981039346656037ull;for(auto b:bytes)checksum=(checksum^b)*1099511628211ull;
    if(checksum!=expected)fail("checksum mismatch");
    net.data.resize(COUNT);std::memcpy(net.data.data(),bytes.data(),COUNT*sizeof(float));
    for(float v:net.data)if(!std::isfinite(v))fail("non-finite parameter");
    net.policyEncoder.resize(extra);
    if(extra)std::memcpy(net.policyEncoder.data(),bytes.data()+COUNT*sizeof(float),extra*sizeof(float));
    for(float v:net.policyEncoder)if(!std::isfinite(v))fail("non-finite policy encoder parameter");
    if(net.data[O_TEMP]<=0)fail("invalid policy temperature");
    net.moves.clear();const char* names=reinterpret_cast<const char*>(bytes.data()+(COUNT+extra)*sizeof(float));
    for(int i=0;i<P;++i){std::string name(names+i*6,strnlen(names+i*6,6));if(name.size()<4||name.size()>5||!net.moves.emplace(name,i).second)fail("invalid vocabulary");}
    for(int i=0;i<H;++i)for(int j=0;j<K;++j)net.w2t[i*K+j]=net.data[O_W2+j*H+i];
    net.sha=std::string(sha,64);net.path=path.string();net.generation++;
}
void ensure_loaded(){if(net.data.size()!=COUNT)fail("no trained model loaded; Stockfish fallback forbidden");}
std::array<float,N> features_reference(const Position& pos){
    std::array<float,N> x{};Color us=pos.side_to_move();int kings[2]={-1,-1},count[12]={},sumOwn[12]={},sumEnemy[12]={};
    for(int s=0;s<64;++s){Piece p=pos.piece_on(Square(s));if(p==NO_PIECE)continue;int plane=int(type_of(p))-1+(color_of(p)==us?0:6),sq=us==WHITE?s:s^56;x[plane*64+sq]=1;count[plane]++;if(type_of(p)==KING)kings[color_of(p)==us?0:1]=sq;}
    if(kings[0]<0||kings[1]<0)fail("missing king");
    x[768]=1;x[769]=bool(pos.can_castle(us==WHITE?WHITE_OO:BLACK_OO));x[770]=bool(pos.can_castle(us==WHITE?WHITE_OOO:BLACK_OOO));x[771]=bool(pos.can_castle(us==WHITE?BLACK_OO:WHITE_OO));x[772]=bool(pos.can_castle(us==WHITE?BLACK_OOO:WHITE_OOO));
    Square ep=pos.state()->chromatiqueEp;x[773]=ep==SQ_NONE?-1.0f:float((int(file_of(ep))+1)/8.0);x[774]=float(std::min(100,pos.rule50_count())/100.0);x[775]=pos.state()->repetition!=0;
    int af=kings[0]%8,ar=kings[0]/8,bf=kings[1]%8,br=kings[1]/8;
    x[776]=float(af/7.0);x[777]=float(ar/7.0);x[778]=float(bf/7.0);x[779]=float(br/7.0);x[780]=float(std::max(std::abs(af-bf),std::abs(ar-br))/7.0);x[781]=float(std::min({af,7-af,ar,7-ar})/3.0);x[782]=float(std::min({bf,7-bf,br,7-br})/3.0);
    int occupied=0;for(int p=0;p<12;++p){occupied+=count[p];for(int s=0;s<64;++s)if(x[p*64+s]){sumOwn[p]+=std::max(std::abs(s%8-af),std::abs(s/8-ar));sumEnemy[p]+=std::max(std::abs(s%8-bf),std::abs(s/8-br));}x[784+p]=float(count[p]/8.0);if(count[p]){x[796+p]=float(double(sumOwn[p])/count[p]/7.0);x[808+p]=float(double(sumEnemy[p])/count[p]/7.0);}}
    x[783]=float(occupied/32.0);return x;
}

std::array<float,N> features_fast(const Position& pos){
    std::array<float,N> x{};Color us=pos.side_to_move();
    int own=int(pos.square<KING>(us))^(us==WHITE?0:56),enemy=int(pos.square<KING>(~us))^(us==WHITE?0:56);
    int af=own%8,ar=own/8,bf=enemy%8,br=enemy/8,occupied=0;
    for(int plane=0;plane<12;++plane){
        Color color=plane<6?us:~us;Bitboard bb=pos.pieces(color,PieceType(plane%6+1));
        if(us==BLACK)bb=__builtin_bswap64(bb);
        int count=0,nearOwn=0,nearEnemy=0;
        while(bb){int s=int(pop_lsb(bb));x[plane*64+s]=1;++count;
            nearOwn+=std::max(std::abs(s%8-af),std::abs(s/8-ar));
            nearEnemy+=std::max(std::abs(s%8-bf),std::abs(s/8-br));}
        occupied+=count;x[784+plane]=float(count/8.0);
        if(count){x[796+plane]=float(double(nearOwn)/count/7.0);x[808+plane]=float(double(nearEnemy)/count/7.0);}
    }
    x[768]=1;x[769]=bool(pos.can_castle(us==WHITE?WHITE_OO:BLACK_OO));x[770]=bool(pos.can_castle(us==WHITE?WHITE_OOO:BLACK_OOO));
    x[771]=bool(pos.can_castle(us==WHITE?BLACK_OO:WHITE_OO));x[772]=bool(pos.can_castle(us==WHITE?BLACK_OOO:WHITE_OOO));
    Square ep=pos.state()->chromatiqueEp;x[773]=ep==SQ_NONE?-1.0f:float((int(file_of(ep))+1)/8.0);
    x[774]=float(std::min(100,pos.rule50_count())/100.0);x[775]=pos.state()->repetition!=0;
    x[776]=float(af/7.0);x[777]=float(ar/7.0);x[778]=float(bf/7.0);x[779]=float(br/7.0);
    x[780]=float(std::max(std::abs(af-bf),std::abs(ar-br))/7.0);
    x[781]=float(std::min({af,7-af,ar,7-ar})/3.0);x[782]=float(std::min({bf,7-bf,br,7-br})/3.0);x[783]=float(occupied/32.0);
    return x;
}
bool reference_eval(){static bool reference=std::getenv("CHROMATIQUE_EVAL_REFERENCE")!=nullptr;return reference;}
std::array<float,N> features(const Position& pos){return reference_eval()?features_reference(pos):features_fast(pos);}

void first_layer_previous(const Position& pos,const std::array<float,N>& x,std::array<float,H>& h,float& direct){
    const float* w=net.data.data();for(int j=0;j<H;++j)h[j]=w[O_B1+j];direct=w[O_LBIAS];
    Color us=pos.side_to_move();
    // Exactly the same ascending feature order and floating arithmetic as the
    // reference, but skip known-zero piece-square slots without scanning768.
    for(int plane=0;plane<12;++plane){
        Bitboard bb=pos.pieces(plane<6?us:~us,PieceType(plane%6+1));if(us==BLACK)bb=__builtin_bswap64(bb);
        while(bb){int i=plane*64+int(pop_lsb(bb));direct+=w[O_LINEAR+i];const float* column=w+i*H;
            for(int j=0;j<H;++j)h[j]+=column[j];}
    }
    for(int i=768;i<N;++i)if(x[i]!=0){float v=x[i];direct+=w[O_LINEAR+i]*v;const float* column=w+i*H;for(int j=0;j<H;++j)h[j]+=column[j]*v;}
    for(float& v:h)v=std::max(0.0f,v);
}

void first_layer_full(const Position& pos,const std::array<float,N>& x,std::array<float,H>& h,float& direct){
    static const bool reference=std::getenv("CHROMATIQUE_FIRST_LAYER_REFERENCE")!=nullptr;
    if(reference){first_layer_previous(pos,x,h,direct);return;}
    const float* w=net.data.data();direct=w[O_LBIAS];
    std::array<int,64> pieceIndices;int pieces=0;
    std::array<int,N-768> tailIndices;int tails=0;
    // Retain the reference's ascending feature order, including the learned
    // direct path. Piece activations are exactly one; state features use FMA.
    Color us=pos.side_to_move();
    for(int plane=0;plane<12;++plane){
        Bitboard bb=pos.pieces(plane<6?us:~us,PieceType(plane%6+1));
        if(us==BLACK)bb=__builtin_bswap64(bb);
        while(bb){int i=plane*64+int(pop_lsb(bb));pieceIndices[pieces++]=i;direct+=w[O_LINEAR+i];}
    }
    for(int i=768;i<N;++i)if(x[i]!=0){tailIndices[tails++]=i;direct+=w[O_LINEAR+i]*x[i];}
    // A tile stays local across all active input columns, reducing repeated
    // loads/stores of the full hidden activation vector. No sum reassociation.
    for(int base=0;base<H;base+=64){
        alignas(16) float acc[64];
        for(int j=0;j<64;++j)acc[j]=w[O_B1+base+j];
        for(int k=0;k<pieces;++k){
            const float* column=w+pieceIndices[k]*H+base;
            for(int j=0;j<64;++j)acc[j]+=column[j];
        }
        for(int k=0;k<tails;++k){
            int i=tailIndices[k];float v=x[i];const float* column=w+i*H+base;
            for(int j=0;j<64;++j)acc[j]+=column[j]*v;
        }
        for(int j=0;j<64;++j)h[base+j]=std::max(0.0f,acc[j]);
    }
}


bool incremental_verify(){static const bool verify=std::getenv("CHROMATIQUE_INCREMENTAL_VERIFY")!=nullptr;return verify;}
struct IncrementalMetrics {
    std::atomic<unsigned long long> hits{0},updates{0},refreshes{0},checks{0};
    std::atomic<unsigned long long> tailColumns{0},fullTailColumns{0};
    std::atomic<double> maximumError{0};
};
IncrementalMetrics incrementalMetrics;
struct PieceAccumulator {
    Key key=0;unsigned generation=0;Color color=WHITE;unsigned refreshDistance=0;
    std::array<float,H> value{};
    std::array<float,N-768> tail{};
};
// Thread-owned; roots/history states remain read-only during evaluation.
thread_local std::array<PieceAccumulator,256> pieceAccumulators;



void first_layer_fast(const Position& pos,const std::array<float,N>& x,std::array<float,H>& h,float& direct){
    static const bool reference=std::getenv("CHROMATIQUE_INCREMENTAL_REFERENCE")!=nullptr;
    if(reference){first_layer_full(pos,x,h,direct);return;}
    const float* w=net.data.data();Color us=pos.side_to_move();direct=w[O_LBIAS];
    std::array<int,64> pieces;int count=0;std::array<int,N-768> tails;int tailCount=0;
    for(int plane=0;plane<12;++plane){
        Bitboard bb=pos.pieces(plane<6?us:~us,PieceType(plane%6+1));if(us==BLACK)bb=__builtin_bswap64(bb);
        while(bb){int i=plane*64+int(pop_lsb(bb));pieces[count++]=i;direct+=w[O_LINEAR+i];}
    }
    // The learned direct path retains canonical feature order and arithmetic.
    for(int i=768;i<N;++i)if(x[i]!=0){tails[tailCount++]=i;direct+=w[O_LINEAR+i]*x[i];}
    const StateInfo* current=pos.state();auto& target=pieceAccumulators[current->key&255];
    auto matches=[&](const PieceAccumulator& a,Key key){return a.key==key&&a.generation==net.generation&&a.color==us;};
    bool boardHit=matches(target,current->key);const PieceAccumulator* ancestor=boardHit?&target:nullptr;
    unsigned distance=boardHit?target.refreshDistance:0;
    std::array<int,16> columns;int columnsCount=0;
    if(!boardHit){
        const StateInfo* path[4];int length=0;const StateInfo* state=current;
        while(length<4&&state->previous){
            path[length++]=state;state=state->previous;
            const auto& cached=pieceAccumulators[state->key&255];
            if(matches(cached,state->key)&&cached.refreshDistance+unsigned(length)<=8){ancestor=&cached;break;}
        }
        if(ancestor){
            distance=ancestor->refreshDistance+unsigned(length);
            for(int step=length-1;step>=0;--step)for(int n=0;n<path[step]->chromaDeltaCount;++n){
                int delta=path[step]->chromaPieceDelta[n];int code=std::abs(delta)-1;
                Piece piece=Piece(code/64);int square=code%64;
                int plane=int(type_of(piece))-1+(color_of(piece)==us?0:6);
                int i=plane*64+(us==WHITE?square:square^56);
                columns[columnsCount++]=(delta>0?1:-1)*(i+1);
            }
        }
    }
    // Cache the full pre-ReLU affine vector and its52 dynamic input values.
    // A board-key hit can have different clock/repetition/raw-EP state; compare
    // every dynamic feature, rather than treating that board key as a full hit.
    std::array<int,N-768> changed;std::array<float,N-768> differences;int changedCount=0;
    if(ancestor)for(int i=768;i<N;++i){
        float delta=x[i]-ancestor->tail[i-768];
        if(delta!=0.0f){changed[changedCount]=i;differences[changedCount++]=delta;}
    }
    bool fullHit=boardHit&&changedCount==0;
    if(boardHit&&changedCount){
        // Repeated same-board state changes also consume the drift budget.
        if(distance>=8){ancestor=nullptr;distance=0;}
        else ++distance;
    }
    if(incremental_verify()){
        if(fullHit)incrementalMetrics.hits.fetch_add(1,std::memory_order_relaxed);
        else if(ancestor)incrementalMetrics.updates.fetch_add(1,std::memory_order_relaxed);
        else incrementalMetrics.refreshes.fetch_add(1,std::memory_order_relaxed);
        incrementalMetrics.tailColumns.fetch_add(ancestor?changedCount:tailCount,std::memory_order_relaxed);
        incrementalMetrics.fullTailColumns.fetch_add(tailCount,std::memory_order_relaxed);
    }
    for(int base=0;base<H;base+=64){
        alignas(16) float acc[64];
        for(int j=0;j<64;++j)acc[j]=ancestor?ancestor->value[base+j]:w[O_B1+base+j];
        if(ancestor){
            for(int k=0;k<columnsCount;++k){
                int delta=columns[k];const float* column=w+(std::abs(delta)-1)*H+base;
                if(delta>0){for(int j=0;j<64;++j)acc[j]+=column[j];}
                else{for(int j=0;j<64;++j)acc[j]-=column[j];}
            }
            for(int k=0;k<changedCount;++k){
                float delta=differences[k];const float* column=w+changed[k]*H+base;
                for(int j=0;j<64;++j)acc[j]+=column[j]*delta;
            }
        }else{
            // Canonical refresh is identical to the frozen full-reference path.
            for(int k=0;k<count;++k){const float* column=w+pieces[k]*H+base;for(int j=0;j<64;++j)acc[j]+=column[j];}
            for(int k=0;k<tailCount;++k){int i=tails[k];float v=x[i];const float* column=w+i*H+base;for(int j=0;j<64;++j)acc[j]+=column[j]*v;}
        }
        // Read an ancestor tile before writing, including same-slot collisions.
        if(!fullHit)for(int j=0;j<64;++j)target.value[base+j]=acc[j];
        for(int j=0;j<64;++j)h[base+j]=std::max(0.0f,acc[j]);
    }
    if(!fullHit){
        for(int i=768;i<N;++i)target.tail[i-768]=x[i];
        target.key=current->key;target.generation=net.generation;target.color=us;target.refreshDistance=distance;
    }
}

void first_layer(const Position& pos,const std::array<float,N>& x,std::array<float,H>& h,float& direct){
    if(reference_eval())first_layer_reference(x,h,direct);else first_layer_fast(pos,x,h,direct);
}

float value_layer_tiled(const std::array<float,H>& h,const float* w,float direct){
    static const bool reference=std::getenv("CHROMATIQUE_VALUE_KERNEL_REFERENCE")!=nullptr;
    float value=w[O_VBIAS]+direct;
    if(reference){
        for(int j=0;j<K;++j){float z=w[O_B2+j]+dot(w+O_W2+j*H,h.data());value+=w[O_VALUE+j]*std::max(0.0f,z);}
        return value;
    }
    std::array<float,K> z;
    // Preserve all four original dot-product streams and their final grouping.
    // Tile across eight output neurons so SIMD can exploit independent streams
    // without reassociating floating-point additions within a neuron.
    for(int base=0;base<K;base+=8){
        alignas(16) float a[8]{},b[8]{},c[8]{},d[8]{};
        for(int i=0;i<H;i+=4){
#pragma clang fp contract(off)
            const float* column=net.w2t.data()+i*K+base;
            for(int j=0;j<8;++j){
                a[j]+=column[j]*h[i];b[j]+=column[K+j]*h[i+1];
                c[j]+=column[2*K+j]*h[i+2];d[j]+=column[3*K+j]*h[i+3];
            }
        }
        for(int j=0;j<8;++j)z[base+j]=w[O_B2+base+j]+((a[j]+b[j])+(c[j]+d[j]));
    }
    for(int j=0;j<K;++j)value+=w[O_VALUE+j]*std::max(0.0f,z[j]);
    return value;
}

double raw_centipawns(const Position& pos){
    auto x=features(pos);std::array<float,H> h;float direct;first_layer(pos,x,h,direct);const float* w=net.data.data();float value=value_layer_tiled(h,w,direct);
    if(incremental_verify()){
        std::array<float,H> referenceH;float referenceDirect;first_layer_full(pos,x,referenceH,referenceDirect);
        float referenceValue=value_layer_tiled(referenceH,w,referenceDirect);
        double error=600.0*std::abs(double(value)-double(referenceValue));
        if(!std::isfinite(error)||error>0.02)fail("incremental float32 shadow error exceeds0.02cp: "+std::to_string(error));
        incrementalMetrics.checks.fetch_add(1,std::memory_order_relaxed);
        double old=incrementalMetrics.maximumError.load(std::memory_order_relaxed);
        while(error>old&&!incrementalMetrics.maximumError.compare_exchange_weak(old,error,std::memory_order_relaxed)){}
    }
    return std::clamp(600.0*value,-10000.0,10000.0);
}
std::string benchmark(const Position& pos,int iterations){
    ensure_loaded();iterations=std::clamp(iterations,1,1000000);double sum=0;
    timespec start,end;clock_gettime(CLOCK_THREAD_CPUTIME_ID,&start);
    for(int i=0;i<iterations;++i)sum+=raw_centipawns(pos);
    clock_gettime(CLOCK_THREAD_CPUTIME_ID,&end);double seconds=end.tv_sec-start.tv_sec+(end.tv_nsec-start.tv_nsec)*1e-9;
    std::ostringstream out;out<<std::setprecision(17)<<"chromabench {\"iterations\":"<<iterations<<",\"cpu_seconds\":"<<seconds<<",\"checksum\":"<<sum<<"}";return out.str();
}

double centipawns(const Position& pos){
    ensure_loaded();struct Entry {Key key=0;double cp=0;unsigned generation=0;};static thread_local std::array<Entry,16384> cache;
    Key key=pos.key();auto& entry=cache[key&16383];if(entry.generation==net.generation&&entry.key==key)return entry.cp;
    double cp=raw_centipawns(pos);entry={key,cp,net.generation};return cp;
}
Value evaluate(const Position& pos){return UCIEngine::from_cp(centipawns(pos),pos);}
bool policy_enabled(){const char* p=std::getenv("CHROMATIQUE_POLICY");return !p||std::strcmp(p,"0");}
void independent_policy_first_layer(const std::array<float,N>& x,std::array<float,H>& h){
    // Policy weights never read value accumulators or value-encoder columns.
    const float* w=net.policyEncoder.data();
    for(int j=0;j<H;++j)h[j]=w[N*H+j];
    for(int i=0;i<N;++i)if(x[i]!=0){
        float v=x[i];const float* column=w+i*H;
        for(int j=0;j<H;++j)h[j]+=column[j]*v;
    }
    for(float& v:h)v=std::max(0.0f,v);
}
std::vector<double> policy(const Position& pos,const std::vector<Move>& moves){
    ensure_loaded();auto x=features(pos);std::array<float,H> h;float direct;if(net.policyEncoder.empty())first_layer(pos,x,h,direct);else independent_policy_first_layer(x,h);std::vector<double> scores;const float* w=net.data.data();
    for(Move move:moves){std::string name=UCIEngine::move(move,pos.is_chess960());if(pos.side_to_move()==BLACK){name[1]=char('9'-name[1]+'0');name[3]=char('9'-name[3]+'0');}auto found=net.moves.find(name);if(found==net.moves.end())fail("move outside vocabulary: "+name);int k=found->second;float z=w[O_PBIAS+k]+dot(w+O_POLICY+k*H,h.data());scores.push_back(z/w[O_TEMP]);}return scores;
}

std::string incremental_stats(){
    std::ostringstream s;s<<std::setprecision(17)<<"chroma_incremental {\"hits\":"<<incrementalMetrics.hits.load()
     <<",\"updates\":"<<incrementalMetrics.updates.load()<<",\"refreshes\":"<<incrementalMetrics.refreshes.load()
     <<",\"tail_columns\":"<<incrementalMetrics.tailColumns.load()<<",\"full_tail_columns\":"<<incrementalMetrics.fullTailColumns.load()
     <<",\"shadow_checks\":"<<incrementalMetrics.checks.load()<<",\"max_cp_error\":"<<incrementalMetrics.maximumError.load()<<"}";
    return s.str();
}

std::string metadata(){ensure_loaded();std::ostringstream s;s<<"{\"name\":\"Chromatique v4.1.0\",\"model_sha256\":\""<<net.sha<<"\",\"search_kind\":\"stockfish19_native\",\"evaluation_kind\":\"fully_neural\",\"classical_evaluation\":false,\"fixed_material\":false,\"architecture\":[820,512,32],\"policy_enabled\":"<<(policy_enabled()?"true":"false")<<",\"policy_encoder\":\""<<(net.policyEncoder.empty()?"shared":"independent")<<"\"}";return s.str();}
std::string trace(const Position& pos){ensure_loaded();auto x=features(pos);std::ostringstream s;s<<std::setprecision(17)<<"chromatique {\"cp\":"<<centipawns(pos)<<",\"features\":[";for(int i=0;i<N;++i){if(i)s<<',';s<<x[i];}s<<"],\"internal\":"<<evaluate(pos)<<",\"roundtrip_cp\":"<<UCIEngine::to_cp(evaluate(pos),pos)<<",\"model_sha256\":\""<<net.sha<<"\",\"policy\":[";std::vector<Move> moves;for(Move m:MoveList<LEGAL>(pos))moves.push_back(m);auto logits=policy(pos,moves);for(usize i=0;i<moves.size();++i){if(i)s<<',';s<<"{\"move\":\""<<UCIEngine::move(moves[i],pos.is_chess960())<<"\",\"logit\":"<<logits[i]<<"}";}s<<"]}";return s.str();}
}
