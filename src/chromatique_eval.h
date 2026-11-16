// Chromatique native evaluator integration. GPL-3.0-or-later.
#pragma once
#include <array>
#include <filesystem>
#include <string>
#include <vector>
#include "position.h"
namespace Stockfish::Chromatique {
std::string default_path();
void initialize_executable_path(const std::filesystem::path&);
void load(const std::filesystem::path&);
void ensure_loaded();
std::array<float,820> features(const Position&);
double centipawns(const Position&);
Value evaluate(const Position&);
std::string benchmark(const Position&,int);
std::string trace(const Position&);
std::string metadata();
std::string incremental_stats();
bool policy_enabled();
std::vector<double> policy(const Position&,const std::vector<Move>&);
}
