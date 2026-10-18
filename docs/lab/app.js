/**
 * BaSingSeCriptografy — RSD-S v4 Interactive Cryptanalysis Laboratory Engine
 *
 * Implements exact GF(2^16) polynomial arithmetic (0x1100B), 32x32 Cauchy MDS
 * diffusion, DDT witness verification, v1-vs-v4 fragmentation analysis, and
 * Known-Answer Test (KAT) vector inspection.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.RsdLab = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var GF16_POLY = 0x1100b;
  var GF16_BITS = 16;
  var W = 32;
  var OMEGA = 0x015e;
  var OMEGA_PLUS_ONE = 0x015f;

  var KAT_VECTORS = [
    {
      name: "zeros",
      x: "0",
      y: "0",
      s_hex: "0000000000000000000000000000000000000000000000000000000000000000",
      n_sess: "0",
      output_hex: "6a73a2975c18d0880483b71dfca4a98e64fabc3b470cf0b87a79c401a3ffb64f"
    },
    {
      name: "sequencial",
      x: "1",
      y: "2",
      s_hex: "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
      n_sess: "1",
      output_hex: "38659dbb20ab18e575e635a708bdd67131ab6afefc79b253c246ced16e8a41ac"
    },
    {
      name: "bits_altos",
      x: "28948022309329048855892746252171976963317496166410141009864396001978282409984",
      y: "14474011154664524427946373126085988481658748083205070504932198000989141204992",
      s_hex: "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      n_sess: "18446744073709551615",
      output_hex: "410a7064d587cf1bf9f784f8c6dd2b913798178214231218700020b6e76c7f3f"
    },
    {
      name: "limites_do_campo",
      x: "57896044618658097711785492504343953926634992332820282019728792003956564819948",
      y: "57896044618658097711785492504343953926634992332820282019728792003956564819947",
      s_hex: "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff",
      n_sess: "81985529216486895",
      output_hex: "e03ebb1905f7157fbdc8a7a6c34bb6a3dc2d88085077225be7f98c79cbefeb65"
    }
  ];

  function gfMult(a, b) {
    var result = 0;
    var aa = a & 0xffff;
    var bb = b & 0xffff;
    while (bb > 0) {
      if (bb & 1) {
        result ^= aa;
      }
      bb >>= 1;
      aa <<= 1;
      if (aa & (1 << GF16_BITS)) {
        aa ^= GF16_POLY;
      }
    }
    return result & 0xffff;
  }

  function gfInv(a) {
    var val = a & 0xffff;
    if (val === 0) {
      return 0;
    }
    var result = 1;
    var base = val;
    var exp = (1 << GF16_BITS) - 2;
    while (exp > 0) {
      if (exp & 1) {
        result = gfMult(result, base);
      }
      base = gfMult(base, base);
      exp >>= 1;
    }
    return result;
  }

  var _cauchyCache = null;
  function getCauchyMds32() {
    if (_cauchyCache !== null) {
      return _cauchyCache;
    }
    var matrix = [];
    for (var i = 0; i < W; i++) {
      var row = new Uint16Array(W);
      for (var j = 0; j < W; j++) {
        row[j] = gfInv(i ^ (W + j));
      }
      matrix.push(row);
    }
    _cauchyCache = matrix;
    return matrix;
  }

  function gfMatrixVectorMult(matrix, vec) {
    var n = vec.length;
    var out = new Uint16Array(n);
    for (var i = 0; i < n; i++) {
      var acc = 0;
      var row = matrix[i];
      for (var j = 0; j < n; j++) {
        if (row[j] !== 0 && vec[j] !== 0) {
          acc ^= gfMult(row[j], vec[j]);
        }
      }
      out[i] = acc;
    }
    return out;
  }

  function inspectBitFlip(bitPos, inputScalarIndex) {
    var bit = Math.max(0, Math.min(254, parseInt(bitPos, 10) || 0));
    var scalarIdx = inputScalarIndex === 1 ? 1 : 0;
    var sliceIndexWithinScalar = Math.floor(bit / 16);
    var bitWithinWord = bit % 16;
    var wordSlot = scalarIdx * 16 + sliceIndexWithinScalar;
    var wordDelta = 1 << bitWithinWord;

    var v1Retained = sliceIndexWithinScalar < 8;
    var sboxOutDelta = gfInv(wordDelta);

    var round1DiffVec = new Uint16Array(W);
    round1DiffVec[wordSlot] = sboxOutDelta;
    var mdsOutVec = gfMatrixVectorMult(getCauchyMds32(), round1DiffVec);

    var activeAfterMds = 0;
    var mdsWordsHex = [];
    for (var i = 0; i < W; i++) {
      if (mdsOutVec[i] !== 0) {
        activeAfterMds++;
      }
      mdsWordsHex.push("0x" + mdsOutVec[i].toString(16).padStart(4, "0"));
    }

    return {
      bit: bit,
      scalar: scalarIdx === 0 ? "x" : "y",
      sliceIndexWithinScalar: sliceIndexWithinScalar,
      bitWithinWord: bitWithinWord,
      wordSlot: wordSlot,
      wordDelta: wordDelta,
      wordDeltaHex: "0x" + wordDelta.toString(16).padStart(4, "0"),
      v1Retained: v1Retained,
      sboxOutDelta: sboxOutDelta,
      sboxOutDeltaHex: "0x" + sboxOutDelta.toString(16).padStart(4, "0"),
      activeWordsRound1: 1,
      activeWordsAfterMds: activeAfterMds,
      branchSum: 1 + activeAfterMds,
      mdsWordsHex: mdsWordsHex
    };
  }

  function verifyDdtMaxWitnesses(deltaIn) {
    var delta = Math.max(1, Math.min(65535, parseInt(deltaIn, 10) || 1));
    var expectedDeltaOut = gfInv(delta);
    var witnesses = [
      0,
      delta,
      gfMult(delta, OMEGA),
      gfMult(delta, OMEGA_PLUS_ONE)
    ];
    var verified = witnesses.map(function (w) {
      var left = gfInv(w);
      var right = gfInv(w ^ delta);
      var diff = left ^ right;
      return {
        witness: w,
        witnessHex: "0x" + w.toString(16).padStart(4, "0"),
        leftInvHex: "0x" + left.toString(16).padStart(4, "0"),
        rightInvHex: "0x" + right.toString(16).padStart(4, "0"),
        outputDiffHex: "0x" + diff.toString(16).padStart(4, "0"),
        matchesMaxTransition: diff === expectedDeltaOut
      };
    });
    return {
      deltaIn: delta,
      deltaInHex: "0x" + delta.toString(16).padStart(4, "0"),
      expectedDeltaOut: expectedDeltaOut,
      expectedDeltaOutHex: "0x" + expectedDeltaOut.toString(16).padStart(4, "0"),
      ddtCount: 4,
      probability: "2^-14 (4 / 65536)",
      witnesses: verified
    };
  }

  function computeWideTrailBound(rounds) {
    var r = Math.max(1, Math.min(255, parseInt(rounds, 10) || 4));
    var pairs = Math.floor(r / 2);
    var rem = r % 2;
    var minActive = pairs * 33 + rem;
    return {
      rounds: r,
      minActiveSboxes: minActive,
      diffLog2Upper: -14 * minActive,
      linearCorrLog2Upper: -7 * minActive,
      linearBiasLog2Upper: -7 * minActive - 1
    };
  }

  function initBrowserUi() {
    if (typeof document === "undefined") {
      return;
    }

    var bitInput = document.getElementById("bit-pos-input");
    var scalarSelect = document.getElementById("scalar-select");
    var v1Status = document.getElementById("v1-truncation-status");
    var v4Status = document.getElementById("v4-coverage-status");
    var wordGrid = document.getElementById("state-word-grid");
    var liveAnnouncement = document.getElementById("lab-live-status");

    function renderBitFlip() {
      if (!bitInput || !scalarSelect || !wordGrid) {
        return;
      }
      var info = inspectBitFlip(bitInput.value, parseInt(scalarSelect.value, 10));

      if (v1Status) {
        if (info.v1Retained) {
          v1Status.className = "status-box pass";
          v1Status.innerHTML =
            '<span class="status-title">v1–v3 (128-bit Slicing): Bit Retained</span>' +
            "Bit #" +
            info.bit +
            " falls in slice #" +
            info.sliceIndexWithinScalar +
            " (bits 0..127). Included in v1 state, though v1 still fails due to rank-5 matrix.";
        } else {
          v1Status.className = "status-box fail";
          v1Status.innerHTML =
            '<span class="status-title">v1–v3 BUG: SILENTLY DROPPED (0% Diffusion)</span>' +
            "Bit #" +
            info.bit +
            " is in slice #" +
            info.sliceIndexWithinScalar +
            " (bits 128..254). v1–v3 only sliced 8 words (128 bits), causing 2^127 trivial collisions!";
        }
      }

      if (v4Status) {
        v4Status.className = "status-box pass";
        v4Status.innerHTML =
          '<span class="status-title">v4 Official (512-bit State): Full F_p Coverage</span>' +
          "Activates Word[" +
          info.wordSlot +
          "] (Δ_in = " +
          info.wordDeltaHex +
          " → S-Box Δ_out = " +
          info.sboxOutDeltaHex +
          ") → Propagates to " +
          info.activeWordsAfterMds +
          "/32 active words after Cauchy MDS (Branch sum = " +
          info.branchSum +
          ").";
      }

      wordGrid.innerHTML = "";
      for (var w = 0; w < W; w++) {
        var cell = document.createElement("div");
        var isTargetWord = w === info.wordSlot;
        var inDroppedV1Region = (w >= 8 && w < 16) || w >= 24;
        cell.className =
          "word-cell " +
          (isTargetWord ? "active-r1" : "active-mds") +
          (inDroppedV1Region ? " dropped-v1" : "");
        cell.innerHTML =
          '<span class="word-idx">W[' +
          w +
          "]" +
          (inDroppedV1Region ? " (v4+)" : "") +
          "</span>" +
          info.mdsWordsHex[w];
        wordGrid.appendChild(cell);
      }

      if (liveAnnouncement) {
        liveAnnouncement.textContent =
          "Updated bit " +
          info.bit +
          " on scalar " +
          info.scalar +
          ": Word " +
          info.wordSlot +
          " active, diffusing to " +
          info.activeWordsAfterMds +
          " MDS words.";
      }
    }

    if (bitInput && scalarSelect) {
      bitInput.addEventListener("input", renderBitFlip);
      scalarSelect.addEventListener("change", renderBitFlip);
      var presetBtns = document.querySelectorAll("[data-bit-preset]");
      presetBtns.forEach(function (btn) {
        btn.addEventListener("click", function () {
          presetBtns.forEach(function (b) {
            b.setAttribute("aria-pressed", "false");
          });
          btn.setAttribute("aria-pressed", "true");
          bitInput.value = btn.getAttribute("data-bit-preset");
          renderBitFlip();
        });
      });
      renderBitFlip();
    }

    // S-Box DDT Inspector
    var deltaInput = document.getElementById("ddt-delta-input");
    var ddtTableBody = document.getElementById("ddt-witness-tbody");
    var ddtSummary = document.getElementById("ddt-summary-line");

    function renderDdt() {
      if (!deltaInput || !ddtTableBody) {
        return;
      }
      var res = verifyDdtMaxWitnesses(deltaInput.value);
      if (ddtSummary) {
        ddtSummary.textContent =
          "Input Difference Δ_in = " +
          res.deltaInHex +
          " → Max Output Difference Δ_out = Inv(Δ_in) = " +
          res.expectedDeltaOutHex +
          " | Exact DDT Multiplicity = " +
          res.ddtCount +
          " (" +
          res.probability +
          ")";
      }
      ddtTableBody.innerHTML = "";
      res.witnesses.forEach(function (row, idx) {
        var tr = document.createElement("tr");
        tr.innerHTML =
          '<td class="mono">#' +
          (idx + 1) +
          "</td>" +
          '<td class="mono">' +
          row.witnessHex +
          "</td>" +
          '<td class="mono">' +
          row.leftInvHex +
          "</td>" +
          '<td class="mono">' +
          row.rightInvHex +
          "</td>" +
          '<td class="mono">' +
          row.outputDiffHex +
          "</td>" +
          '<td class="mono">' +
          (row.matchesMaxTransition ? "✓ SAT (4/65536)" : "✗") +
          "</td>";
        ddtTableBody.appendChild(tr);
      });
    }

    if (deltaInput) {
      deltaInput.addEventListener("input", renderDdt);
      renderDdt();
    }

    // KAT Vector Selector
    var katSelect = document.getElementById("kat-vector-select");
    var katDetails = document.getElementById("kat-vector-details");
    function renderKat() {
      if (!katSelect || !katDetails) {
        return;
      }
      var idx = parseInt(katSelect.value, 10) || 0;
      var v = KAT_VECTORS[idx] || KAT_VECTORS[0];
      katDetails.innerHTML =
        "<div><strong>Vector Name:</strong> <code>" +
        v.name +
        "</code></div>" +
        "<div><strong>x ∈ F_p:</strong> <code>" +
        v.x +
        "</code></div>" +
        "<div><strong>y ∈ F_p:</strong> <code>" +
        v.y +
        "</code></div>" +
        "<div><strong>Key s (32B hex):</strong> <code>" +
        v.s_hex +
        "</code></div>" +
        "<div><strong>Session n_sess:</strong> <code>" +
        v.n_sess +
        "</code></div>" +
        '<div class="digest-out"><strong>Expected v4 SHA-256 Digest:</strong><br>' +
        v.output_hex +
        "</div>";
    }
    if (katSelect) {
      katSelect.addEventListener("change", renderKat);
      renderKat();
    }
  }

  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", initBrowserUi);
    } else {
      initBrowserUi();
    }
  }

  return {
    GF16_POLY: GF16_POLY,
    KAT_VECTORS: KAT_VECTORS,
    gfMult: gfMult,
    gfInv: gfInv,
    getCauchyMds32: getCauchyMds32,
    gfMatrixVectorMult: gfMatrixVectorMult,
    inspectBitFlip: inspectBitFlip,
    verifyDdtMaxWitnesses: verifyDdtMaxWitnesses,
    computeWideTrailBound: computeWideTrailBound
  };
});
