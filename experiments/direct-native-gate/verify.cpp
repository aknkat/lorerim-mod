#include "cooldown_core.hpp"

#include <atomic>
#include <iostream>
#include <limits>
#include <memory>
#include <random>
#include <stdexcept>
#include <thread>
#include <vector>

using lks::design::Cooldown;
using lks::design::Decision;
using lks::design::LoadResult;
using lks::design::Request;
constexpr Request own{true, true, true};
constexpr std::uint64_t second = 1'000'000'000ULL;
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

void spam_and_boundary() {
    Cooldown g;
    require(g.admit_final(own) == Decision::admit_owned, "first cast");
    for (unsigned i = 0; i < 60'000; ++i) {
        require(g.query(own) == Decision::block_owned, "query must not unlock");
        require(g.admit_final(own) == Decision::block_owned, "spam must reject");
        g.advance(1'000'000, true);
    }
    require(g.remaining() == 0, "rejected attempts must not extend 60 seconds");
    require(g.admit_final(own) == Decision::admit_owned, "60 second boundary");
    g.advance(std::numeric_limits<std::uint64_t>::max(), true);
    require(g.remaining() == 0, "large elapsed time must saturate, not underflow");
}

void pause_and_restart() {
    Cooldown before;
    require(before.admit_final(own) == Decision::admit_owned, "initial cast");
    before.advance(15 * second, true);
    before.advance(12 * 60 * 60 * second, false);
    require(before.remaining() == 45 * second, "pause must not consume cooldown");
    const auto saved = before.save();
    Cooldown after; // Fresh instance; no old process timestamp or callback.
    require(after.load(1, saved) == LoadResult::restored, "restore format");
    after.advance(44 * second, true);
    require(after.query(own) == Decision::block_owned, "saved remaining time");
    after.advance(second, true);
    require(after.query(own) == Decision::admit_owned, "restore must expire");
    const auto ready = after.save();
    Cooldown ready_after_restart;
    require(ready_after_restart.load(1, ready) == LoadResult::restored, "ready load");
    require(ready_after_restart.query(own) == Decision::admit_owned, "ready on load");
}

void scope_and_recovery() {
    Cooldown g;
    for (bool player : {false, true})
        for (bool khajiit : {false, true})
            require(g.admit_final({false, player, khajiit}) == Decision::forward_other,
                    "foreign spells must pass through");
    require(g.admit_final({true, false, true}) == Decision::block_owned, "NPC guard");
    require(g.admit_final({true, true, false}) == Decision::block_owned, "race guard");
    require(g.remaining() == 0, "unrelated/rejected requests changed state");
    require(g.admit_final(own) == Decision::admit_owned, "owned cast");
    for (unsigned i = 0; i < 100'000; ++i) (void)g.query(own);
    require(g.remaining() == 60 * second, "preview/check must be read-only");
    const Cooldown::Bytes too_large{255, 255, 255, 255, 255, 255, 255, 255};
    require(g.load(1, too_large) == LoadResult::invalid_reinitialized, "invalid payload");
    g.advance(60 * second, true);
    require(g.remaining() == 0, "invalid load must not create permanent lock");
    require(g.load(99, {}) == LoadResult::invalid_reinitialized, "invalid version");
    g.clear();
    require(g.remaining() == 0, "revert must not leak another save's cooldown");
}

void simultaneous_admission() {
    Cooldown g;
    std::atomic<unsigned> accepted{};
    std::atomic<bool> start{};
    {
        std::vector<std::jthread> workers;
        for (unsigned i = 0; i < 32; ++i)
            workers.emplace_back([&] {
                while (!start.load()) std::this_thread::yield();
                if (g.admit_final(own) == Decision::admit_owned) ++accepted;
            });
        start.store(true);
    }
    require(accepted.load() == 1, "simultaneous requests must accept exactly once");
}

void independent_timeline_oracle() {
    // Oracle stores an absolute deadline; the core stores a decreasing duration.
    // Only this oracle has a session epoch, which changes on simulated restart.
    std::mt19937_64 rng(0x4C4B53);
    auto g = std::make_unique<Cooldown>();
    std::uint64_t now{}, deadline{}, saved_remaining{};
    auto saved = g->save();
    auto remaining = [&] { return deadline > now ? deadline - now : 0; };
    auto expected = [&](Request r) {
        if (!r.owned_spell) return Decision::forward_other;
        return r.player && r.khajiit && remaining() == 0
            ? Decision::admit_owned : Decision::block_owned;
    };
    for (unsigned i = 0; i < 200'000; ++i) {
        const Request r{rng() % 4 != 0, rng() % 4 != 0, rng() % 4 != 0};
        switch (rng() % 7) {
        case 0: case 1: {
            const auto delta = rng() % (5 * second);
            const bool running = rng() % 3 != 0;
            g->advance(delta, running);
            if (running) now += delta;
            break;
        }
        case 2: {
            const auto result = expected(r);
            require(g->admit_final(r) == result, "oracle admission mismatch");
            if (result == Decision::admit_owned) deadline = now + 60 * second;
            break;
        }
        case 3:
            require(g->query(r) == expected(r), "oracle query mismatch");
            break;
        case 4:
            saved_remaining = remaining();
            saved = g->save();
            break;
        case 5:
            g = std::make_unique<Cooldown>();
            require(g->load(1, saved) == LoadResult::restored, "oracle reload");
            now = rng() % (10'000'000 * second); // Different process epoch.
            deadline = now + saved_remaining;
            break;
        case 6:
            g->clear();
            deadline = now;
            break;
        }
        require(g->remaining() == remaining(), "oracle remaining-time mismatch");
    }
}

int main() {
    spam_and_boundary();
    pause_and_restart();
    scope_and_recovery();
    simultaneous_admission();
    independent_timeline_oracle();
    std::cout << "5 scenario groups passed; 200000 randomized timeline operations.\n"
                 "Standalone core only: no Skyrim hooks, engine timing, rendering or DLL verified.\n";
}
