package com.tariff.tariff_backend.controller;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import com.tariff.tariff_backend.dto.CountryDTO;
import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyRequest;
import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyResponse;
import com.tariff.tariff_backend.dto.CalculationDTO.TransactionLineDTO;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.repository.TariffRepo;
import com.tariff.tariff_backend.service.CalculationService;
import com.tariff.tariff_backend.service.CalculatorHistoryService;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;


@RestController
@RequestMapping("/api/v1/tariffs")
@Tag(name = "Tariff Calculator", description = "Browse and search tariff data with country filtering and duty calculations")
public class TariffBrowseController {

    // Fill the FROM dropdown (distinct partner countries present in tariffs)
    private final TariffRepo repo;
    private final CalculationService calcService;
    private final CalculatorHistoryService calcHistService;

    public TariffBrowseController(TariffRepo repo, CalculationService calcService, CalculatorHistoryService calcHistService) {
        this.repo = repo;
        this.calcService = calcService;
        this.calcHistService = calcHistService;
    }

    @Operation(
        summary = "Get available partner countries",
        description = "Retrieves list of countries that can be used as 'from' (partner) countries in tariff searches. Optionally filtered by destination country."
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "List of available partner countries",
            content = @Content(mediaType = "application/json", 
                schema = @Schema(type = "array", implementation = CountryDTO.class)))
    })
    @GetMapping("/countries/partners")
    public List<CountryDTO> fromCountries(
        @Parameter(description = "Optional destination country ID to filter available partners", example = "840")
        @RequestParam(required = false) Integer toId) {
        if (toId != null) {
            return repo.availableFromByTo(toId);
        }
        return repo.availableFrom();
    }

    @Operation(
        summary = "Get available reporter countries", 
        description = "Retrieves list of countries that can be used as 'to' (reporter) countries in tariff searches. Optionally filtered by source country."
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "List of available reporter countries",
            content = @Content(mediaType = "application/json", 
                schema = @Schema(type = "array", implementation = CountryDTO.class)))
    })
    @GetMapping("/countries/reporters")
    public List<CountryDTO> toCountries(
        @Parameter(description = "Optional source country ID to filter available destinations", example = "156")
        @RequestParam(required = false) Integer fromId) {
        return repo.availableTo(fromId);
    }

    @Operation(
        summary = "Search tariffs",
        description = "Search tariffs with optional filtering by source country, destination country, and text query. Returns paginated results with metadata."
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Paginated search results with tariff data",
            content = @Content(mediaType = "application/json", 
                schema = @Schema(type = "object", 
                    example = "{\n" +
                             "  \"content\": [],\n" +
                             "  \"number\": 0,\n" +
                             "  \"size\": 10,\n" +
                             "  \"totalPages\": 5,\n" +
                             "  \"totalElements\": 50,\n" +
                             "  \"last\": false\n" +
                             "}")))
    })
    @GetMapping("/search")
    public Map<String, Object> search(
            @Parameter(description = "Source/partner country ID", example = "156")
            @RequestParam(required = false) Integer fromId,
            @Parameter(description = "Destination/reporter country ID", example = "840")
            @RequestParam(required = false) Integer toId,
            @Parameter(description = "Search query for product description or codes", example = "wheat")
            @RequestParam(required = false) String q,
            @Parameter(description = "Page number (0-based)", example = "0")
            @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Number of items per page", example = "10")
            @RequestParam(defaultValue = "10") int size) {

        String query = (q == null || q.trim().isEmpty()) ? null : q.trim();
        Page<Tariff> result = repo.searchNative(fromId, toId, query, PageRequest.of(page, size));

        Map<String, Object> response = new HashMap<>();
        response.put("content", result.getContent());
        response.put("number", result.getNumber());
        response.put("size", result.getSize());
        response.put("totalPages", result.getTotalPages());
        response.put("totalElements", result.getTotalElements());
        response.put("last", result.isLast());

        return response;
    }

    @Operation(
        summary = "Calculate duty amount",
        description = "Calculates customs duty based on tariff rates and transaction details. Stores the calculation for future reference."
    )
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "Duty calculation completed successfully",
            content = @Content(mediaType = "application/json", schema = @Schema(implementation = CalculateDutyResponse.class)))
    })
    @PostMapping("/calc")
    public ResponseEntity<CalculateDutyResponse> calculate(
        @Parameter(description = "Calculation request with transaction details", required = true)
        @RequestBody CalculateDutyRequest req) {
        return ResponseEntity.ok(calcService.calculateAndStore(req));
    }

    @GetMapping("/transactionHistory")
    public List<TransactionLineDTO> getHistory(){
        return calcHistService.viewHistory();
    }

    @DeleteMapping("/transactionHistory/{transactionId}")
    public ResponseEntity<Void> deleteTransaction(@PathVariable Integer transactionId, Authentication auth){
        if (auth == null | auth.getName() == null){
            return ResponseEntity.status(401).build();
        }
        calcHistService.deleteOwn(transactionId, auth);
        return ResponseEntity.noContent().build();
    }
    
    @DeleteMapping("/transactionHistory")
    public ResponseEntity<Void> bulkDelete(@RequestParam("ids") String idsCsv, Authentication auth) {
    if (auth == null || auth.getName() == null) return ResponseEntity.status(401).build();

    for (String s : idsCsv.split(",")) {     // e.g. "12, 18, 25"
        String t = s.trim();
        if (!t.isEmpty()) {
            try { calcHistService.deleteOwn(Integer.parseInt(t), auth); }
            catch (NumberFormatException ignored) {}
        }
    }
    return ResponseEntity.noContent().build(); // 204
    }
    
}
