package com.tariff.tariff_backend.repository;

import com.tariff.tariff_backend.model.tariffs_new.Tariff;
import com.tariff.tariff_backend.dto.CountryDTO;
import com.tariff.tariff_backend.model.tariffs_new.Country;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;

public interface TariffRepo extends JpaRepository<Tariff, String>, JpaSpecificationExecutor<Tariff> {

  Optional<Tariff> findByTariffId(String tariffId);

  List<Tariff> findByDescriptionwcountry(String descriptionwcountry);

  List<Tariff> findByPartnerCountry(Country partnerCountry);

  List<Tariff> findByReporterCountry(Country reporterCountry);

  List<Tariff> findByUnitname(String unitname);

  List<Tariff> findByCategory(String category);

  List<Tariff> findByAdValorem(BigDecimal adValorem);

  List<Tariff> findBySpecificPerUnit(BigDecimal specificPerUnit);

  // Partial search
  List<Tariff> findByDescriptionwcountryContainingIgnoreCase(String keyword);

  // ---------- SEARCH ----------
  @Query(value = """
      SELECT * FROM tariffs.tariff_master t
      WHERE (:fromId IS NULL OR t.partnercountry = :fromId)
        AND (:toId   IS NULL OR t.reportercountry = :toId)
        AND (:q IS NULL OR LOWER(t.descriptionwcountry) LIKE LOWER(CONCAT('%', :q, '%'))
                        OR t.tariffid LIKE CONCAT('%', :q, '%'))
        AND (:yearFrom IS NULL OR t.year >= :yearFrom)
        AND (:yearTo   IS NULL OR t.year <= :yearTo)
      """, countQuery = """
      SELECT COUNT(*) FROM tariffs.tariff_master t
      WHERE (:fromId IS NULL OR t.partnercountry = :fromId)
        AND (:toId   IS NULL OR t.reportercountry = :toId)
        AND (:q IS NULL OR LOWER(t.descriptionwcountry) LIKE LOWER(CONCAT('%', :q, '%'))
                        OR t.tariffid LIKE CONCAT('%', :q, '%'))
        AND (:yearFrom IS NULL OR t.year >= :yearFrom)
        AND (:yearTo   IS NULL OR t.year <= :yearTo)
      """, nativeQuery = true)
  Page<Tariff> searchNative(
      @Param("fromId") Integer fromId,
      @Param("toId") Integer toId,
      @Param("q") String q,
      @Param("yearFrom") Integer yearFrom,
      @Param("yearTo") Integer yearTo,
      Pageable pageable);

  // ---------- DROPDOWNS ----------

  // FROM countries = distinct partnercountry present in tariffs
  @Query(value = """
      select distinct c.countryid as id, c.iso2, c.name
      from tariffs.tariff_master t
      join tariffs.country c on c.countryid = t.partnercountry
      order by c.name
      """, nativeQuery = true)
  List<Object[]> availableFromRaw();

  // TO countries = distinct reportercountry, optionally filtered by chosen FROM
  @Query(value = """
      select distinct c.countryid as id, c.iso2, c.name
      from tariffs.tariff_master t
      join tariffs.country c on c.countryid = t.reportercountry
      where (:fromId is null or t.partnercountry = :fromId)
      order by c.name
      """, nativeQuery = true)
  List<Object[]> availableToRaw(@Param("fromId") Integer fromId);

  // NEW: FROM countries filtered by chosen TO
  @Query(value = """
      select distinct c.countryid as id, c.iso2, c.name
      from tariffs.tariff_master t
      join tariffs.country c on c.countryid = t.partnercountry
      where (:toId is null or t.reportercountry = :toId)
      order by c.name
      """, nativeQuery = true)
  List<Object[]> availableFromRawByTo(@Param("toId") Integer toId);

  Page<Tariff> findByTariffId(String tariffid, Pageable pageable);

  Page<Tariff> findByDescriptionwcountryContainingIgnoreCase(String q, Pageable pageable);
  // ---------- Convenience DTO mappers ----------

  default List<CountryDTO> availableFrom() {
    return availableFromRaw().stream()
        .map(a -> new CountryDTO(((Number) a[0]).intValue(), (String) a[1], (String) a[2]))
        .toList();
  }

  default List<CountryDTO> availableTo(Integer fromId) {
    return availableToRaw(fromId).stream()
        .map(a -> new CountryDTO(((Number) a[0]).intValue(), (String) a[1], (String) a[2]))
        .toList();
  }

  default List<CountryDTO> availableFromByTo(Integer toId) {
    return availableFromRawByTo(toId).stream()
        .map(a -> new CountryDTO(((Number) a[0]).intValue(), (String) a[1], (String) a[2]))
        .toList();
  }
}