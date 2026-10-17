#pragma once

// Design experiment only. No Skyrim hook, DLL, ESP or Papyrus implementation.
// The adapter MUST call admit_final once per accepted, new, physical cast,
// before effect application. Queries and restoration are not new casts.
#include <array>
#include <cstdint>
#include <mutex>
#include <span>

namespace lks::design {
struct Request {
    bool owned_spell;
    bool player;
    bool khajiit;
};
enum class Decision { forward_other, block_owned, admit_owned };
enum class LoadResult { restored, invalid_reinitialized };

class Cooldown {
public:
    static constexpr std::uint64_t duration_ns = 60'000'000'000ULL;
    static constexpr std::uint32_t wire_version = 1;
    using Bytes = std::array<std::uint8_t, 8>;

    Decision query(Request r) const {
        const std::lock_guard lock(mutex_);
        return decide(r);
    }

    Decision admit_final(Request r) {
        const std::lock_guard lock(mutex_);
        const auto result = decide(r);
        if (result == Decision::admit_owned) remaining_ = duration_ns;
        return result;
    }

    // Input is validated, unscaled, active-game elapsed time. This class does
    // NOT establish how Skyrim supplies it or which menus pause the game.
    void advance(std::uint64_t active_delta_ns, bool gameplay_running) {
        const std::lock_guard lock(mutex_);
        if (gameplay_running)
            remaining_ -= active_delta_ns < remaining_ ? active_delta_ns : remaining_;
    }

    std::uint64_t remaining() const {
        const std::lock_guard lock(mutex_);
        return remaining_;
    }

    Bytes save() const {
        const std::lock_guard lock(mutex_);
        Bytes bytes{};
        for (unsigned i = 0; i < bytes.size(); ++i)
            bytes[i] = static_cast<std::uint8_t>(remaining_ >> (i * 8));
        return bytes;
    }

    LoadResult load(std::uint32_t version, std::span<const std::uint8_t> bytes) {
        const std::lock_guard lock(mutex_);
        if (version != wire_version || bytes.size() != 8) {
            remaining_ = duration_ns;
            return LoadResult::invalid_reinitialized;
        }
        std::uint64_t restored{};
        for (unsigned i = 0; i < bytes.size(); ++i)
            restored |= static_cast<std::uint64_t>(bytes[i]) << (i * 8);
        if (restored > duration_ns) {
            remaining_ = duration_ns;
            return LoadResult::invalid_reinitialized;
        }
        remaining_ = restored;
        return LoadResult::restored;
    }

    // New game / revert, or no record on first installation. Losing a co-save
    // cannot reconstruct the prior cooldown; that is not a normal restore.
    void clear() {
        const std::lock_guard lock(mutex_);
        remaining_ = 0;
    }

private:
    Decision decide(Request r) const {
        if (!r.owned_spell) return Decision::forward_other;
        if (!r.player || !r.khajiit || remaining_ != 0) return Decision::block_owned;
        return Decision::admit_owned;
    }
    mutable std::mutex mutex_;
    std::uint64_t remaining_{};
};
} // namespace lks::design
