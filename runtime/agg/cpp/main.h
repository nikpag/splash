// See instructions below this include block
#include <string>
#include <istream>

// -*-*-*-*-*-*-*-*-*-* INSTRUCTIONS BEGIN HERE -*-*-*-*-*-*-*-*-*-*
// This file contains common code between all aggregators
// It should be included when implementing a new aggregator
// It contains the aggregator's main function
// To use it, just include it and implement the function presented below
// and remember to link the executable with main.cpp

void aggregate() noexcept; // implement this

// It should work in the following manner:
// 1. It should request inputs to aggregate when it needs them using
//    objects returned by the functions below:

[[nodiscard]] std::istream& input1() noexcept;
[[nodiscard]] std::istream& input2() noexcept;

// 2. It should output the aggregated results as soon as it has a piece
//    of them done to the stream returned to function below:

[[nodiscard]] std::ostream& output() noexcept;