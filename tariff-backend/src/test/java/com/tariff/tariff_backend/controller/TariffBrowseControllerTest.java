// src/test/java/com/tariff/tariff_backend/controller/TariffBrowseControllerTest.java
package com.tariff.tariff_backend.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tariff.tariff_backend.config.ApplicationConfig;
import com.tariff.tariff_backend.config.CorsConfig;
import com.tariff.tariff_backend.config.SecurityConfiguration;
import com.tariff.tariff_backend.dto.CountryDTO;
import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyRequest;
import com.tariff.tariff_backend.dto.CalculationDTO.CalculateDutyResponse;
import com.tariff.tariff_backend.dto.CalculationDTO.TransactionLineDTO;
import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.repository.TariffRepo;
import com.tariff.tariff_backend.security.JwtAuthenticationEntryPoint;
import com.tariff.tariff_backend.security.JwtAuthenticationFilter;
import com.tariff.tariff_backend.service.CalculationService;
import com.tariff.tariff_backend.service.CalculatorHistoryService;
import com.tariff.tariff_backend.service.JwtService;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.http.MediaType;
import org.springframework.security.core.Authentication;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal; // <-- IMPORT ADDED
import java.time.Instant; // <-- IMPORT ADDED
import java.util.Collections;
import java.util.List; // <-- IMPORT ADDED

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post; // <-- IMPORT ADDED
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete; // <-- IMPORT ADDED
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(TariffBrowseController.class)
@Import({
    SecurityConfiguration.class, 
    CorsConfig.class,
    JwtAuthenticationEntryPoint.class,
    JwtAuthenticationFilter.class
})
public class TariffBrowseControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper; // <-- ADDED for request bodies

    @MockBean
    private TariffRepo repo;

    @MockBean
    private CalculationService calcService;

    @MockBean
    private CalculatorHistoryService calcHistService;

    @MockBean
    private JwtService jwtService;

    @MockBean
    private ApplicationConfig applicationConfig;


    // --- Tests for /countries/partners ---
    
    @Test
    @WithMockUser
    public void testGetPartnerCountries_NoFilter() throws Exception {
        when(repo.availableFrom()).thenReturn(Collections.emptyList());

        mockMvc.perform(get("/api/v1/tariffs/countries/partners"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray());
    }

    @Test
    @WithMockUser
    public void testGetPartnerCountries_WithToIdFilter() throws Exception {
        when(repo.availableFromByTo(840)).thenReturn(Collections.emptyList());

        mockMvc.perform(get("/api/v1/tariffs/countries/partners")
                        .param("toId", "840"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray());
    }

    // --- Tests for /countries/reporters ---

    @Test
    @WithMockUser
    public void testGetReporterCountries_WithFromIdFilter() throws Exception {
        when(repo.availableTo(123)).thenReturn(Collections.emptyList());

        mockMvc.perform(get("/api/v1/tariffs/countries/reporters")
                        .param("fromId", "123"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray());
    }
    
    @Test
    @WithMockUser
    public void testGetReporterCountries_NoFilter() throws Exception {
        when(repo.availableTo(null)).thenReturn(Collections.emptyList());

        mockMvc.perform(get("/api/v1/tariffs/countries/reporters"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$").isArray());
    }

    // --- Tests for /search ---

    @Test
    @WithMockUser
    public void testSearch_WithAllParams() throws Exception {
        Tariff mockTariff = new Tariff();
        Page<Tariff> resultPage = new PageImpl<>(Collections.singletonList(mockTariff), Pageable.ofSize(10), 1);

        when(repo.searchNative(
                eq(156), eq(840), eq("wheat"), eq(2020), eq(2023), any(Pageable.class)
        )).thenReturn(resultPage);

        mockMvc.perform(get("/api/v1/tariffs/search")
                        .param("fromId", "156")
                        .param("toId", "840")
                        .param("q", "wheat")
                        .param("yearFrom", "2020")
                        .param("yearTo", "2023")
                        .param("page", "0")
                        .param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(1));
    }
    
    @Test
    @WithMockUser
    public void testSearch_WithNullParams() throws Exception {
        Page<Tariff> resultPage = new PageImpl<>(Collections.emptyList(), Pageable.ofSize(10), 0);

        // Test with all optional params as null
        when(repo.searchNative(
                eq(null), eq(null), eq(null), eq(null), eq(null), any(Pageable.class)
        )).thenReturn(resultPage);

        mockMvc.perform(get("/api/v1/tariffs/search")
                        .param("page", "0")
                        .param("size", "10"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(0));
    }
    
    @Test
    @WithMockUser
    public void testSearch_WithBlankQuery() throws Exception {
        Page<Tariff> resultPage = new PageImpl<>(Collections.emptyList(), Pageable.ofSize(10), 0);

        // Test query string that is just whitespace, should be treated as null
        when(repo.searchNative(
                eq(null), eq(null), eq(null), eq(null), eq(null), any(Pageable.class)
        )).thenReturn(resultPage);

        mockMvc.perform(get("/api/v1/tariffs/search")
                        .param("q", "   ")) // Blank query
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.totalElements").value(0));
    }

    // --- Tests for /calc ---
    
    @Test
    @WithMockUser
    public void testCalculate() throws Exception {
        CalculateDutyRequest request = new CalculateDutyRequest("t1", null, null, false);
        CalculateDutyResponse response = new CalculateDutyResponse(1, "t1", BigDecimal.ZERO);

        when(calcService.calculateAndStore(any(CalculateDutyRequest.class))).thenReturn(response);

        mockMvc.perform(post("/api/v1/tariffs/calc")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.transactionId").value(1));
    }

    // --- Tests for /transactionHistory ---

    @Test
    @WithMockUser
    public void testGetHistory() throws Exception {
        TransactionLineDTO tx = new TransactionLineDTO(1, Instant.now(), Collections.emptyMap());
        when(calcHistService.viewHistory()).thenReturn(List.of(tx));

        mockMvc.perform(get("/api/v1/tariffs/transactionHistory"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].transactionId").value(1));
    }

    @Test
    @WithMockUser
    public void testDeleteTransaction_Success() throws Exception {
        doNothing().when(calcHistService).deleteOwn(anyInt(), any(Authentication.class));

        mockMvc.perform(delete("/api/v1/tariffs/transactionHistory/{transactionId}", 123))
                .andExpect(status().isNoContent()); // 204
    }
    
    @Test
    public void testDeleteTransaction_Unauthorized() throws Exception {
        // No @WithMockUser means auth is null
        mockMvc.perform(delete("/api/v1/tariffs/transactionHistory/{transactionId}", 123))
                .andExpect(status().isUnauthorized()); // 401
    }

    @Test
    @WithMockUser
    public void testBulkDelete_Success() throws Exception {
        doNothing().when(calcHistService).deleteOwn(anyInt(), any(Authentication.class));

        mockMvc.perform(delete("/api/v1/tariffs/transactionHistory")
                        .param("ids", "1, 2, 3"))
                .andExpect(status().isNoContent());
                
        verify(calcHistService, times(3)).deleteOwn(anyInt(), any(Authentication.class));
    }
    
    @Test
    @WithMockUser
    public void testBulkDelete_WithBadData() throws Exception {
         mockMvc.perform(delete("/api/v1/tariffs/transactionHistory")
                        .param("ids", "1, abc, , 4")) // Should skip "abc" and ""
                .andExpect(status().isNoContent());
                
        // Verifies delete was called for "1" and "4", but not for "abc" or ""
        verify(calcHistService, times(1)).deleteOwn(eq(1), any(Authentication.class));
        verify(calcHistService, times(1)).deleteOwn(eq(4), any(Authentication.class));
        verify(calcHistService, times(2)).deleteOwn(anyInt(), any(Authentication.class));
    }
    
    @Test
    public void testBulkDelete_Unauthorized() throws Exception {
        // No @WithMockUser means auth is null
        mockMvc.perform(delete("/api/v1/tariffs/transactionHistory")
                        .param("ids", "1, 2, 3"))
                .andExpect(status().isUnauthorized()); // 401
    }
}